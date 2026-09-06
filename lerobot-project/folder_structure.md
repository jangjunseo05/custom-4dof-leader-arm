# lerobot-project 폴더 구조

생성일: 2026-07-27

```
lerobot-project/
├── .devcontainer/
│   ├── Dockerfile
│   └── devcontainer.json
├── config/
│   └── config.yaml
├── datasets/                     (비어 있음)
├── notebooks/                    (비어 있음)
├── preprocess/                   (비어 있음)
├── raw_data/
│   ├── actions/                  (비어 있음)
│   ├── end_effector_pose/        (비어 있음)
│   ├── force_torque/             (비어 있음)
│   ├── images/                   (비어 있음)
│   ├── joint_states/             (비어 있음)
│   └── timestamps/               (비어 있음)
├── rosbag/                       (비어 있음)
└── src/
    ├── __pycache__/              (컴파일 캐시, 무시 가능)
    ├── config_loader.py
    ├── data_loader.py
    ├── episode_builder.py
    ├── exporter.py
    ├── main.py
    └── synchronizer.py
```

## 요약

- **config/**: 설정 파일(`config.yaml`) 보관
- **raw_data/**: 원시 데이터 저장용 하위 폴더 구조만 존재 (actions, end_effector_pose, force_torque, images, joint_states, timestamps) — 현재 파일 없음
- **datasets/**, **notebooks/**, **preprocess/**, **rosbag/**: 현재 비어 있는 폴더
- **src/**: 실제 파이썬 소스 코드
  - `config_loader.py` — 설정 로딩
  - `data_loader.py` — 데이터 로딩
  - `episode_builder.py` — 에피소드 구성
  - `exporter.py` — 데이터 내보내기
  - `main.py` — 진입점
  - `synchronizer.py` — 동기화 처리
- **.devcontainer/**: VS Code Dev Container 설정 (`Dockerfile`, `devcontainer.json`)
