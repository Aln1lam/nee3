#!/usr/bin/env python
"""测试流量捕获代理功能"""

import requests
import json
import time
import sys

BASE_URL = 'http://localhost:5000/api'

def test_login():
    """测试登录"""
    print("[1] Testing login...")
    response = requests.post(f'{BASE_URL}/auth/login', json={
        'account': 'Alnilam',
        'password': '123456'
    })
    
    print(f"Response status: {response.status_code}")
    print(f"Response content: {response.text}")
    
    if response.status_code == 200:
        data = response.json()
        token = data.get('access_token') or data.get('data', {}).get('access_token')
        if token:
            print(f"✓ Login successful, token: {token[:30]}...")
            return token
        else:
            print(f"✗ No token in response: {data}")
            sys.exit(1)
    else:
        print(f"✗ Login failed: {response.status_code}")
        print(response.text)
        sys.exit(1)

def test_get_challenges(token):
    """获取题目列表"""
    print("\n[2] Getting challenges...")
    headers = {'Authorization': f'Bearer {token}'}
    
    # 尝试不同的端点
    endpoints = [
        f'{BASE_URL}/challenges',
        'http://localhost:5000/challenges',
        'http://localhost:5000/api/challenges/list'
    ]
    
    for endpoint in endpoints:
        print(f"  Trying {endpoint}...")
        response = requests.get(endpoint, headers=headers)
        
        if response.status_code == 200:
            challenges = response.json()
            if isinstance(challenges, dict):
                challenges = challenges.get('data', [])
            
            print(f"✓ Found {len(challenges)} challenges")
            
            for c in challenges[:3]:
                print(f"  - id={c['id']} title={c['title']} docker={c.get('docker_image', 'N/A')}")
            
            # 返回有docker_image的题目
            docker_challenges = [c for c in challenges if c.get('docker_image')]
            if docker_challenges:
                return docker_challenges[0]
            return challenges[0] if challenges else None
    
    print(f"✗ All endpoints failed")
    return None

def test_start_container(token, challenge):
    """启动容器并测试流量捕获"""
    if not challenge:
        print("\n[3] Skipping container test (no docker challenge)")
        return
    
    challenge_id = challenge['id']
    print(f"\n[3] Starting container for challenge {challenge_id}...")
    
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.post(f'{BASE_URL}/challenges/{challenge_id}/start-container', headers=headers)
    
    if response.status_code == 200:
        data = response.json()['data']
        print(f"✓ Container started")
        print(f"  Instance ID: {data['instance_id']}")
        print(f"  Connection URL: {data['connection_url']}")
        print(f"  Port: {data['port']}")
        
        # 检查是否启用了流量捕获
        if challenge.get('enable_traffic_capture'):
            print(f"✓ Traffic capture is enabled")
            # 给代理一点时间启动
            time.sleep(1)
            
            # 检查PCAP文件是否被创建
            from pathlib import Path
            pcap_dir = Path('captures')
            if pcap_dir.exists():
                pcap_files = list(pcap_dir.glob('**/*.pcap'))
                print(f"  Found {len(pcap_files)} PCAP files")
                if pcap_files:
                    print(f"  Latest: {pcap_files[-1].relative_to(pcap_dir)}")
        else:
            print(f"⚠ Traffic capture is NOT enabled for this challenge")
        
        return data
    else:
        print(f"✗ Failed to start container: {response.status_code}")
        print(response.text)
        return None

if __name__ == '__main__':
    print("=== Testing Traffic Capture Proxy ===\n")
    
    try:
        token = test_login()
        challenge = test_get_challenges(token)
        test_start_container(token, challenge)
        
        print("\n=== Test Complete ===")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
