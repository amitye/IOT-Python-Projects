Using generic Hardware components and RaspberryPi, I have connected different sensors such as temperature, light, proximity, sound, gyro, accelerator and more.
The sensor_data_to_aws.py script is reading the sensor data and reporting it to an AWS topic. The frequency of the updates can be modified through AWS Shadow.

Similar devices with similar sensing capabilities, were located in different areas in the same space. I used Elasticsearch services in order to create alerts from all sensing devices regarding extreme mesurements which vary according to the sensors. 
For example, suspiciously high average temperature might indicate a fire.
