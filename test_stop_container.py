#!/usr/bin/env python
"""测试停止容器的权限问题"""

import requests
import json

BASE_URL = 'http://localhost:5000/api'

def test_stop_container():
    """测试停止容器"""
    # 1. 登录
    response = requests.post(f'{BASE_URL}/auth/login', json={
        'account': 'Alnilam',
        'password': '123456'
    })
    
    if response.status_code != 200:
        print(f"✗ Login failed: {response.status_code}")
        return
    
    token = response.json().get('access_token')
    print(f"✓ Login successful")
    
    # 2. 停止容器
    headers = {'Authorization': f'Bearer {token}'}
    instance_id = 46
    
    print(f"\n[TEST] Stopping instance {instance_id}...")
    response = requests.post(
        f'{BASE_URL}/challenges/instances/{instance_id}/stop',
        headers=headers
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response:\n{json.dumps(response.json(), indent=2, ensure_ascii=False)}")

if __name__ == '__main__':
    test_stop_container()
