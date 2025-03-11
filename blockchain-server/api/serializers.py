from rest_framework import serializers

class TransactionSerializer(serializers.Serializer):
    candidate = serializers.CharField(required=True)
    voterhash = serializers.CharField(required=True)
    timestamp = serializers.CharField(read_only=True)

    def validate_voterhash(self, value):
        if not value:
            raise serializers.ValidationError("Voter hash cannot be empty")
        return value

class BlockSerializer(serializers.Serializer):
    index = serializers.IntegerField(required=True)
    transactions = TransactionSerializer(many=True)
    timestamp = serializers.CharField(required=True)
    previous_hash = serializers.CharField(required=True)
    nonce = serializers.IntegerField(required=True)
    blockhash = serializers.CharField(required=True, write_only=True)

class ChainSerializer(serializers.Serializer):
    length = serializers.IntegerField()
    chain = BlockSerializer(many=True)
    peers = serializers.ListField(child=serializers.CharField())

class NodeRegistrationSerializer(serializers.Serializer):
    node_address = serializers.CharField(required=True)

    def validate_node_address(self, value):
        if not value:
            raise serializers.ValidationError("Node address cannot be empty")
        return value

class MessageResponseSerializer(serializers.Serializer):
    message = serializers.CharField()

class ErrorResponseSerializer(serializers.Serializer):
    error = serializers.CharField()