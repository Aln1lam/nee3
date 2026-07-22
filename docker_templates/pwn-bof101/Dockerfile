FROM python:3.11-slim

WORKDIR /opt/chal
COPY challenge.py /opt/chal/challenge.py
COPY flag.txt /flag

EXPOSE 9999

# 常驻 TCP 服务；裸 ubuntu+bash 会立刻 Exit 0，端口映射存在但无进程监听
CMD ["python", "-u", "/opt/chal/challenge.py"]
