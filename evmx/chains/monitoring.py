import asyncio
import json
import os
import sys
from pathlib import Path

import django
from django.core.cache import cache
from loguru import logger
from web3.datastructures import AttributeDict
from web3.types import HexStr

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()

from chains.models import Block
from chains.models import Chain
from chains.tasks import filter_and_store_tx


async def get_block_data(chain: Chain, block_identifier: HexStr | int) -> AttributeDict:
    return await chain.async_w3.eth.get_block(block_identifier, full_transactions=True)


async def get_block_data_batch(
    chain: Chain,
    block_identifiers: list[HexStr | int],
) -> list[AttributeDict]:
    """
    通过协程,异步获取批量区块数据
    :param chain:
    :param block_identifiers:
    :return:
    """
    get_block_data_tasks = [
        get_block_data(chain, block_identifier)
        for block_identifier in block_identifiers
    ]
    block_datas = await asyncio.gather(*get_block_data_tasks)

    # 对区块数据按照区块号进行排序

    return sorted(block_datas, key=lambda x: x["number"])


async def get_parent_block(chain: Chain, parent_hash: HexStr) -> Block | None:
    """
    只有缺失数量不多的情况下,才会进入此追溯父块的函数,因为此函数会发生递归调用,需控制深度;
    根据父区块的哈希值获取数据库对应的 Block,若不存在,则创建父区块;
    :param chain: 区块网络
    :param parent_hash: 父块哈希值
    :return: 父 Block;如果是新系统干净无区块,则返回 None
    """
    try:
        return await Block.objects.aget(hash=parent_hash)

    except Block.DoesNotExist:
        if await chain.block_set.aexists():
            parent_data = await get_block_data(chain, parent_hash)
            return await store_block_with_txs(chain, parent_data)

        return None


async def store_block_with_txs(chain: Chain, block_data: AttributeDict) -> Block:
    """
    将本区块和它的交易入库;
    :param block_data:
    :param chain:
    :return: Block
    """
    await Block.objects.filter(
        chain=chain,
        number__gte=block_data["number"],
    ).adelete()  # 删除同网络中所有大于等于本区块号的区块
    parent_block = await get_parent_block(chain, block_data["parentHash"].hex())

    block_obj: Block = await Block.objects.acreate(
        hash=block_data["hash"].hex(),
        parent=parent_block,
        number=block_data["number"],
        chain=chain,
        timestamp=block_data["timestamp"],
    )

    for tx in block_data["transactions"]:
        filter_and_store_tx.delay(
            chain.chain_id,
            block_obj.number,
            json.loads(chain.w3.to_json(tx)),
        )

    logger.info(f"{block_data['number']}  {block_data['hash'].hex()} ok")

    return block_obj


async def monitor_the_chain(chain: Chain):
    """
    监控区块链网络;
    当数据库中的 Chain 数据发生变化时,结束本次监控任务;
    监控过程中,需要判断数据库的最新区块,是否大幅落后于区块链,如果是的话,需要运行区块补齐逻辑,未落后则将当前最新区块入库;
    :param chain:
    :return: None
    """
    while True:
        if cache.get("chains_changed", False):
            logger.info(f"检测到链发生数据变更,重启{chain.name}监控")
            return

        try:
            block_filter = await chain.async_w3.eth.filter("latest")
            while True:
                new_block_hashes = await block_filter.get_new_entries()
                new_block_data_batch = await get_block_data_batch(
                    chain,
                    new_block_hashes,
                )

                (
                    need_aligned,
                    align_from_numer,
                    align_to_numer,
                ) = await chain.need_aligned(new_block_data_batch)

                if need_aligned:
                    new_block_data_batch = await get_block_data_batch(
                        chain,
                        list(range(align_from_numer, align_to_numer)),
                    )

                for (
                    new_block_data
                ) in new_block_data_batch:  # 此处需要保证必须按照从小到大的顺序插入区块
                    await store_block_with_txs(chain, new_block_data)

                if cache.get("chains_changed", False):
                    logger.info(f"检测到链发生数据变更,重启{chain.name}监控")
                    return
                await asyncio.sleep(1)

        except asyncio.CancelledError:
            return
        except Exception as e:
            msg = f"Error in monitor_the_chain {chain.name}: {e}"
            logger.error(msg)
            await asyncio.sleep(1)


async def main():
    """
    主函数,持续运行;
    任务组的任务全部 return,说明数据库网络被修改,需要重新载入 Chain 参数进行监控;
    :return:
    """
    while True:
        try:
            chains = Chain.objects.filter(active=True)
            cache.set(key="chains_changed", value=False)
            async with asyncio.TaskGroup() as task_group:
                async for chain in chains:
                    task_group.create_task(monitor_the_chain(chain))
                    logger.info(f"{chain.name} 监控启动成功")

        except asyncio.CancelledError:
            return
        await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
