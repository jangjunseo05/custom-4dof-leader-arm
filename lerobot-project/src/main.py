from config_loader import ConfigLoader
from data_loader import DataLoader


def main():
    # config.yaml 읽기
    loader = ConfigLoader()

    # 설정 가져오기
    config = loader.get()

    # 확인 출력
    print("=" * 50)
    print("설정 파일을 정상적으로 읽었습니다.")
    print("=" * 50)

    print(f"Robot Name : {config['robot']['name']}")
    print(f"Image Topic : {config['topics']['image']}")
    print(f"Joint Topic : {config['topics']['joint_state']}")
    print(f"Force Topic : {config['topics']['force_torque']}")
    print(f"Output Folder : {config['output']['raw_data']}")
    data_loader = DataLoader(config["output"]["raw_data"])
    data_loader.check_folder()
    data_loader.show_folders()

if __name__ == "__main__":
    main()
    

    # synchronizer → validator.validate_raw → episode_builder → stats → exporter → validator.validate_final_dataset