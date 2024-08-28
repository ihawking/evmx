#!/bin/bash

# 检查 .env 文件是否已存在
if [ -f .env ]; then
    echo ".env 文件已存在。"
    exit 0
fi

# 生成随机字符串的函数
generate_random_string() {
    local length=$1
    local result=""
    while [ ${#result} -lt $length ]; do
        result+=$(openssl rand -base64 32 | tr -dc 'a-zA-Z0-9' | cut -c -$((length - ${#result})))
    done
    echo "$result"
}

# 创建 .env 文件
echo "正在创建 .env 文件..."

# 生成随机的 POSTGRES_PASSWORD (32 字符长)
POSTGRES_PASSWORD=$(generate_random_string 32)

# 生成随机的 DJANGO_SECRET_KEY (32 字符长)
DJANGO_SECRET_KEY=$(generate_random_string 64)

# 将生成的值写入 .env 文件
cat << EOF > .env
POSTGRES_PASSWORD=$POSTGRES_PASSWORD
DJANGO_SECRET_KEY=$DJANGO_SECRET_KEY
EOF

echo ".env 文件已成功创建!"
