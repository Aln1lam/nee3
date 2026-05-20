#!/usr/bin/env python
"""直接测试流量捕获代理启动"""

import requests
import time
import json
from pathlib import Path

BASE_URL = 'http://localhost:5000/api'

def login():
    """登录"""
    response = requests.post(f'{BASE_URL}/auth/login', json={
        'account': 'Alnilam',
        'password': '123456'
    })
    
    if response.status_code == 200:
        data = response.json()
        token = data.get('access_token')
        print(f"✓ Login successful")
        return token
    else:
        print(f"✗ Login failed: {response.status_code}")
        return None

def test_container_start(token, challenge_id=4):
    """测试启动容器"""
    print(f"\n[TEST] Starting container for challenge {challenge_id}...")
    
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.post(
        f'{BASE_URL}/challenges/{challenge_id}/start-container',
        headers=headers
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response:\n{json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        data = response.json()
        if data.get('code') == 200:
            info = data.get('data', {})
            instance_id = info.get('instance_id')
            proxy_port = info.get('port')  # 这可能是临时的
            connection_url = info.get('connection_url')
            
            print(f"\n✓ Container started successfully:")
            print(f"  Instance ID: {instance_id}")
            print(f"  Connection URL: {connection_url}")
            print(f"  Port: {proxy_port}")
            
            # 等待代理启动
            print(f"\nWaiting for proxy to start...")
            time.sleep(2)
            
            # 检查PCAP文件
            pcap_dir = Path('captures')
            if pcap_dir.exists():
                pcap_files = list(pcap_dir.glob('**/*.pcap'))
                print(f"\n✓ Found {len(pcap_files)} PCAP files:")
                for f in pcap_files[-3:]:
                    size = f.stat().st_size
                    print(f"  - {f.relative_to(pcap_dir)} ({size} bytes)")
            
            return instance_id
        else:
            print(f"✗ Error: {data.get('msg')}")
            return None
    else:
        print(f"✗ Request failed")
        return None

if __name__ == '__main__':
    print("=== Testing TCP Traffic Capture Proxy ===\n")
    
    token = login()
    if token:
        test_container_start(token)
