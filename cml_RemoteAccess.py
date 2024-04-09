# -*- coding: utf-8 -*-
#!/usr/bin/env python3
'''
This script is used to install RADKit on an existing CML lab. Using this script, one can swiftly make their CML lab accessible remotely from anywhere. Leverages the power of CML APIs through virl2_client it auto installs and configures RADKit service on an existing CML lab. 
'''
import netmiko
import getpass
import time
import re
 
# For testing I am using virl2_client version 2.6.1. Check the version of virl2_client in your environment and update the version accordingly.
# You may find your compatible client version at https://<Your CML Server>/client/
#pip install virl2_client==2.6.1
#pip install netmiko==4.3.0
from virl2_client import ClientLibrary
 
VIRL_CONTROLLER = "" # Your CML Server URL goes here for example: https://cml.demo.dcloud.cisco.com/
VIRL_USERNAME = "" # Your CML Username
VIRL_PASSWORD = getpass.getpass("CML Password: ") # Your CML Password
VIRL_WORKBENCH = "" # Your exisiting lab name where you want to install RADKit
 
# Download the latest Linux x86 based RADKit installer, say cisco_radkit_1.6.6_linux_x86_64.sh,from https://radkit.cisco.com/downloads/release
# Move the downloaded installer to a web server where your CML can access it
# Your CML should be able to access the RADKit Linux installer from a web server. In this case I am using a dCloud workstation as an example
RADKIT_INSTALLER = "http://workstation.demo.dcloud.cisco.com/cisco_radkit_1.6.6_linux_x86_64.sh"
 
# Provide your Cisco SSO that will be used for the RADKit enrollment
CISCO_SSO = "your-cisco-sso"

 
# Provide the OTP for the RADKit enrollment. This is a one-time password that is generated from your RADKit account
# To generate a Service OTP, go to the system where you already have a RADKit Client installed.
# Login to the client and generate OTP by running the following 2 commands:
#c = sso_login("<your Cisco SSO>")
#c.grant_client_otp()
# Copy the OTP from the output, which will be something like PROD:1234-5678-9012
# Everytime to run this script, you have to have a new OTP to go with it
RADKIT_OTP = "PROD:1234-1234-1234" # Change this to your OTP

# DONE WITH THE CONFIGURATION. DO NOT CHANGE ANYTHING BELOW THIS LINE
# ---------------------------------------------------------------------

# Connecting to the CML instance
try:
    client = ClientLibrary(VIRL_CONTROLLER, VIRL_USERNAME, VIRL_PASSWORD, ssl_verify=False)
except:
    print("Failed to connect to CML instance")
    exit(1)
# Check if the CML instance is ready
client.is_system_ready(wait=True)
print("Connected to the CML... Let's Go!")
 
#Get the lab where we want to add RADKit
print("Accessing the lab..")
try:
    lab = client.find_labs_by_title(VIRL_WORKBENCH)[0]
except:
    print("Failed to find the lab")
    exit(1)
 
# Create external connection for radkit_service
print("Creating desired nodes in the lab..")
e1 = lab.create_node("radkit_ext_service","external_connector",0,200)
 
# Adding Unmanaged Switch in between with 16 ports
s1 = lab.create_node("radkit_unmanaged_switch","unmanaged_switch",100,300)
s1.create_interface(16)
 
# Create a Ubuntu Node where RADKit will be installed 
u1 = lab.create_node("radkit_service_radcml","ubuntu",200,200)
 
# Lets add the config to the Ubuntu node
u1.config = "\
#cloud-config\n\
hostname: radkit_radcml\n\
manage_etc_hosts: True\n\
system_info:\n\
  default_user:\n\
    name: cisco\n\
password: cisco\n\
chpasswd: { expire: False }\n\
ssh_pwauth: True\n\
ssh_authorized_keys:\n\
   - your-ssh-pubkey-line-goes-here\n\
runcmd:\n\
- apt-get update -y\n\
- chown -R cisco:cisco /home/cisco\n\
- apt install -y make build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev git\n\
- netplan apply\n\
\n\
write_files:\n\
- path: /home/cisco/.bash_profile\n\
  content: |\n\
    export PATH=$PATH:~/.local/bin\n\
    export RADKIT_SERVICE_SUPERADMIN_PASSWORD_BASE64=\"$( echo -n 'Cisco123!' | base64 )\"\n\
  owner: root:root\n\
  permissions: '0644'\n\
- path: /etc/netplan/50-cloud-init.yaml\n\
  content: |\n\
          network:\n\
              ethernets:\n\
                  ens2:\n\
                      dhcp4: true\n\
                      dhcp6: false\n\
  owner: root:root\n\
  permissions: '0644'\n\
"
 
# Connecting all three nodes
lab.connect_two_nodes(s1, e1)
lab.connect_two_nodes(s1, u1)
 
# Lets start the lab. 
print("Starting the lab..")
lab.start() 
print("Lab started successfully..")
# Sleep 1 additional min for Ubuntu to load the cloud-config
#time.sleep(60)
print("Moving forward with connecting to the newly created Ubuntu...")
 
# Now connecting to ubuntu via netmiko connection
VIRL_HOST = re.search(r'(?:https?://)?([^/\s]+)(?:.*)',VIRL_CONTROLLER).group(1)
print(f"Now attempting to connect to your CML Console Server at {VIRL_HOST}")
c = netmiko.ConnectHandler(device_type='terminal_server',
                        host=VIRL_HOST,
                        username=VIRL_USERNAME,
                        password=VIRL_PASSWORD)
c.write_channel('\r')
c.write_channel(f'open /{lab.title}/{u1.label}/0\r')
time.sleep(120)
c.write_channel('\r')
time.sleep(1)
c.write_channel('\r')
time.sleep(1)
output = c.read_channel()
max_loops = 10
i = 1
while i <= max_loops:
    output = c.read_channel()
 
    if 'login:' in output:
        c.write_channel('cisco' + '\r')
        time.sleep(1)
        output = c.read_channel()
 
    # Search for password pattern / send password
    if 'assword' in output:
        c.write_channel('cisco' + '\r')
        time.sleep(.5)
        output = c.read_channel()
        # Did we successfully login
 
    if '$' in output or '#' in output:
        print("Successful login")
        break
 
    c.write_channel('\r')
    time.sleep(.5)
    i += 1
 
netmiko.redispatch(c, device_type='linux')
c.find_prompt()
 
print(f"Attempting to download the RADKit installer on the Ubuntu server from {RADKIT_INSTALLER}...")
try:
    result = c.send_command_timing(f'wget {RADKIT_INSTALLER}',read_timeout=1200)
except:
    print("FAILED: Unable to download the RADKit installer from the internal server. Please confirm your lab has access RADKit installer "+RADKIT_INSTALLER+" and try again")
    exit(1)
 
print("Preparing the RADKit installer...")
try:
    installer_file = RADKIT_INSTALLER.split("/")[-1]
    result = c.send_command(f'chmod +x /home/cisco/{installer_file}')
except:
    print("FAILED: Unable to download and extract the RADKit installer from the server. Please confirm your lab has access to the RADKit file and try again")
    exit(1)
 
print("Running the RADKit installer...")
try:
    result = c.send_command_timing(f'/home/cisco/{installer_file} -- --default-install',read_timeout=600)
except:
    print("Hitting exception for running the installer. Will wait for a minute and proceed forward")
    time.sleep(60)
 
print("Bootstraping the RADKit service...")
try:
    result = c.send_command_timing('/home/cisco/.local/bin/radkit-service bootstrap',read_timeout=240)
except:
    print("Hitting exception for running the bootstrap. Will wait for a minute and proceed forward")
    time.sleep(60)
 
print("Enrolling the RADKit service...")
try:
    result = c.send_command_timing('/home/cisco/.local/bin/radkit-service enroll '+RADKIT_OTP,read_timeout=120)
except Exception as e:
    print("Hitting exception on enrollment with error: ")
    print(e)
    time.sleep(60)
if re.search("Certificate enrollment failed",result):
    print(result)
    print("\n\nCertification enrollment failed. Please try again with a new/correct OTP")
    exit(1)
 
print("Starting the RADKit service...")
try:
    result = c.send_command('nohup /home/cisco/.local/bin/radkit-service run --headless &')
except:
    print(result)
    print("\nHitting exception for starting the RADKit service. Will wait for a minute and proceed forward")
    time.sleep(60)
c.write_channel('\r')
 
print("Starting final configurations on your RADKit Service...")
result = c.send_command('mkdir -p /home/cisco/.radkit/control')
 
print("Creating control toml")
c.send_command('echo \'[control]\' > /home/cisco/.radkit/control/settings.toml',expect_string=r'control')
c.send_command('echo \'service_url="https://localhost:8081/api/v1"\' >> /home/cisco/.radkit/control/settings.toml',expect_string='service_url')
c.send_command('echo \'admin_name="superadmin"\' >> /home/cisco/.radkit/control/settings.toml',expect_string='admin_name')
c.send_command('echo \'admin_password="Cisco123!"\' >> /home/cisco/.radkit/control/settings.toml',expect_string='admin_password')
c.send_command('echo \'[control.proxy]\' >> /home/cisco/.radkit/control/settings.toml',expect_string='control')
time.sleep(5)
result = c.send_command('/home/cisco/.local/bin/radkit-control system status',expect_string=r'webserver_sha256_fingerprint')
print(result)
if re.search(r'connected\"\:\s+(\w+)',result):
    conn_status = re.search(r'connected\"\:\s+(\w+)',result).group(1)
    if conn_status == "false":
        print("RADKit Service did you come up. Please try again with a new OTP.")
        exit(1)
    print("RADKit Service is up and running")
if re.search(r'service_id\"\:\s+\"(\w{4}-\w{4}-\w{4})',result):
    service_id = re.search(r'service_id\"\:\s+\"(\w{4}-\w{4}-\w{4})',result).group(1)
    print("Service ID: "+service_id)
else:
    print("Service ID not found. Please try again with a new OTP.")
    exit(1) 
print("Attempting to access service from control")
result = c.send_command('/home/cisco/.local/bin/radkit-control user create '+CISCO_SSO+' --active forever',expect_string=r'create')
print(result)
 
print("Adding RADKit Service as a device so you can access it from RADKit Client")
result = c.send_command('/home/cisco/.local/bin/radkit-control device create radkitservice localhost RADKIT_SERVICE --http-port 443 --http-username superadmin --http-password Cisco123! --http-protocol HTTPS --http-no-verify --forwarded-tcp-ports 8081',expect_string=r'radkit')
 
print(result)
enrollment = "Your RADKIt service is being enrolled. Here are your RADKit Service details:\n\nService ID: "+service_id+"\nUser: superadmin\nPassword: Cisco123!\nPort: 8081\n\nFor more info on how to access your lab through RADKit, you can follow the steps on https://github.com/tariqhab/CML_RemoteAccess/edit/main/README.md"
print(enrollment)
