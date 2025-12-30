# Dummy TorchServe Handler
import logging
def handle(data, context):
    return [{'prediction': 'success'}]