# signup 题目模板

这套目录用于构建动态 flag 的容器题镜像。

## 构建

```bash
docker build -t signup:latest .
```

## 运行

```bash
docker run --rm -p 43974:80 -e FLAG=flag{demo} signup:latest
```

## 说明

- `flag.sh` 会在容器启动时把 `flag{testflag}` 替换成环境变量 `FLAG` 的值。
- 动态题 Flag 模板推荐 `flag{[TEAM_HASH]}`，生成格式如 `flag{550e8400-e29b-41d4-a716-446655440000}`（同队稳定）。
- 比赛容器对外端口默认映射在 **10000–20000**（可通过环境变量 `NEPU_CONTAINER_PORT_MIN/MAX` 调整）。
