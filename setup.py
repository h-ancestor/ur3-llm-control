import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'ur3_llm_control'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Hien',
    maintainer_email='hien@todo.todo',
    description='UR3 LLM Control Assignment',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'llm_planner = ur3_llm_control.llm_planner:main',
            'planning_scene = ur3_llm_control.planning_scene:main',
        ],
    },
)