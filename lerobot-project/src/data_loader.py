from pathlib import Path


class DataLoader:
    """
    raw_data 폴더의 데이터를 읽는 클래스
    """

    def __init__(self, raw_data_path="raw_data"):
        self.raw_data_path = Path(raw_data_path)

    def check_folder(self):
        """
        raw_data 폴더가 존재하는지 확인한다.
        """

        if self.raw_data_path.exists():
            print(f"✅ 폴더를 찾았습니다 : {self.raw_data_path}")
            return True

        else:
            print(f"❌ 폴더를 찾을 수 없습니다 : {self.raw_data_path}")
            return False
        
    def show_folders(self):
        """
        raw_data 폴더 안의 파일과 폴더를 출력한다.
        """

        print("=" * 50)
        print("raw_data 폴더 내용")
        print("=" * 50)

        for item in self.raw_data_path.iterdir():
            print(item)


    def load_image_list(self):
        """
        images 폴더의 PNG 파일 목록을 가져온다.
        """

        image_folder = self.raw_data_path / "images"

        image_list = sorted(image_folder.glob("*.png"))

        print("=" * 50)
        print("이미지 목록")
        print("=" * 50)

        for image in image_list:
            print(image)

        return image_list
    