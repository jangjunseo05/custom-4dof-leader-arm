import os
from glob import glob

from setuptools import find_packages, setup

package_name = "ros_arm"

setup(
    name=package_name,
    version="0.0.1",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        (os.path.join("share", package_name, "launch"), glob("launch/*.launch.py")),
        (os.path.join("share", package_name, "urdf"), glob("urdf/*.urdf")),
        (os.path.join("share", package_name, "rviz"), glob("rviz/*.rviz")),
        (os.path.join("share", package_name, "meshes"), glob("meshes/*.stl")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="jangjunseo",
    maintainer_email="jjs6350@dgu.ac.kr",
    description="4축 로봇암(jdcobot100) URDF 시각화 및 파이썬 UI 조인트 제어 패키지 (문제 1)",
    license="Apache-2.0",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "joint_gui = ros_arm.joint_gui:main",
        ],
    },
)
