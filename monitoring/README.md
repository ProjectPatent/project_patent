# **Network Flow Monitoring 패키지**

**API 호출 모니터링**과 **네트워크 성능**을 목적으로 구성한 패키지. 
주요 기능 : API 호출 속도 제한, 에러 확인, 지연시간 측정. 
Prometheus와 Grafana를 이용하여 시각화해보고자 합니다.

## **목적**
- **API 호출 모니터링**: 데코레이터를 통해 API 호출에 대한 지연 시간 및 에러 발생을 확인.
- **네트워크 상태 모니터링**: API 호출 및 네트워크 관련 메트릭을 Prometheus 익스포터에 저장하여 성능을 시각적으로 분석.

---

## **디렉터리 구조**

```
network_flow_monitoring/
│
├── __init__.py               # 패키지 초기화
├── decorators.py             # API 모니터링을 위한 데코레이터 패턴 
├── prometheus_exporter.py    # Prometheus 익스포터 설정
├── setup.py                  # 패키지 설치 설정
├── README.md                 # 프로젝트 설명 및 사용법
└── requirements.txt          # 필요한 패키지 명세
```

- **decorators.py**: API 호출에 대한 메트릭을 수집하고 에러를 확인할 수 있는 데코레이터.
- **prometheus_exporter.py**: Prometheus 서버에 메트릭을 전송하기 위한 익스포터 설정.

---

## **설치방법**

### **실행 조건**
- `requirements.txt` 파일에 명시된 의존성 설치.
  ```
  pip install -r requirements.txt
  ```

### **패키지 설치**
1. 패키지 디렉터리에서 아래 커맨드로 실행 및 설치.
   ```
   pip install .
   ```

2. 설치 후, Prometheus 익스포터를 통해 모니터링을 시작하려면 아래 커맨드로 실행.
   ```
   start_exporter --port 8000
   ```

---

## **사용법**

### 1. **API 호출 모니터링 적용**
   - 데코레이터를 사용하여, API 호출에 대한 모니터링을 활성화.
   
   ```
   from network_flow_monitoring.decorators import monitor_api_call

   @monitor_api_call
   def example_api_call():
       # API 호출 로직
       pass
   ```

### 2. **Prometheus 익스포터 실행**
   - `start_exporter` 커맨드로 Prometheus 익스포터를 실행하여 메트릭을 수집.
   ```
   start_exporter --port 8000
   ```

   Prometheus 서버에서 해당 포트를 통해 메트릭을 수집, Grafana에서 시각화.

---

## **모듈별 설명**

### 1. `decorators.py`
- **기능**: API 호출 모니터링 데코레이터 제공
- **사용법**:
  ```
  from network_flow_monitoring.decorators import monitor_api_call
  
  @monitor_api_call
  def call_api():
      # API 호출 로직
  ```

### 2. `prometheus_exporter.py`
- **기능**: Prometheus 익스포터 실행 및 메트릭 제공
- **사용법**:
  ```
  start_exporter --port 8000
  ```

---

