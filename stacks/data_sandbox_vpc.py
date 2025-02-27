#// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#// SPDX-License-Identifier: MIT-0

import os
from aws_cdk import (
    aws_ec2 as ec2,
    NestedStack
)
from constructs import Construct


class VPCStack(NestedStack):
    def __init__(self, scope: Construct, id: str, aws_region='', **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        
        #parameters
        vpc_cidr = self.node.try_get_context("vpc_cidr")

        # Build VPC
        self.vpc = ec2.Vpc(self, "vpc",
          ip_addresses=ec2.IpAddresses.cidr(vpc_cidr),
          subnet_configuration=[
              ec2.SubnetConfiguration(name='Isolated', subnet_type=ec2.SubnetType.PRIVATE_ISOLATED)]
          )

        # Build VPC endpoints
        s3_endpoint = self.vpc.add_gateway_endpoint('s3-endpoint',
          service=ec2.GatewayVpcEndpointAwsService('s3')
          )

        ssm_endpoint = self.vpc.add_interface_endpoint("ssm-endpoint",
          service=ec2.InterfaceVpcEndpointAwsService.SSM
          )

        notebook_endpoint = self.vpc.add_interface_endpoint("notebook-endpoint",
          service=ec2.InterfaceVpcEndpointAwsService.SAGEMAKER_NOTEBOOK
          )
