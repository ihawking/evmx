from rest_framework import serializers

from chains.models import Chain


class ChainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chain
        fields = (
            "chain_id",
            "name",
        )
