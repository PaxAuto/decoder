from setuptools import find_packages, setup

package_name = 'decoder'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Harsh Mukeshbhai Bhadani    ',
    maintainer_email='har8774s@hs-coburg.de',
    description='Decoder component subscribing /spat topic from domain bridge and publishing extracted information in /decoder_info ',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
             'decoder_node = decoder.decoder_node:main',
        ],
    },
)
