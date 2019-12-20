# 위치기반 SNS 서비스


### 개요

- 데이터베이스 텀 프로젝트로 만든 위치기반 SNS 서비스입니다.  
- 사용자의 위치를 측정하여 그 위치에 게시글을 남기거나, 주변의 게시글을 확인할 수 있습니다.
- 컴퓨터에 MySQL DB가 없다면 정상적으로 작동하지 않습니다.

---

### 실행 방법

1. python 가상 환경 설치 및 실행

```
python -m venv {venv_name}

{venv_name}\Scripts\activate
```

2. 필요 패키지 다운로드

```
pip install --upgrade pip

pip install -r requirements.txt
```

3. 프로그램 실행

```
python gui.py
```
