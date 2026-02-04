#!/usr/bin/env python3
import os
import sys

# CDK 앱 루트를 sys.path에 추가하여 스택 모듈을 임포트할 수 있게 함
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from aws_cdk import App
from kdp_pipeline_stack import KdpPipelineStack

app = App()

KdpPipelineStack(
    app,
    "KdpPipelineStack",
    env={
        "account": os.getenv("CDK_ACCOUNT", "123456789012"),
        "region": os.getenv("CDK_REGION", "ap-northeast-2"),
    },
)

app.synth()
