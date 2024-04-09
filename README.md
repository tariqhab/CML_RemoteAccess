# Cisco Modeling Lab Remote Connect (CML_RemoteAccess)

**Description:** Experience the unparalleled capabilities of your Cisco Modeling Lab (CML) with ease. You no longer need to use console connection, jump servers, or even breakout tools to access your Cisco Modeling Lab ([CML](https://www.cisco.com/c/en/us/products/cloud-systems-management/modeling-labs/index.html)) setup. Using this script, you can swiftly make your CML lab accessible remotely from anywhere. It leverages CML APIs through virl2_client python library to install and configure RADKit service within your existing lab. Remote Automation and Development Kit ([RADKit](https://radkit.cisco.com/)) is a free of cost package that Cisco offers which is primarily used by TAC to connect to remote network devices for support.

**Setup:**

Before running the script, go over at least the top portion of the script to fill out the variables based on your environment. The detailed instructions are provided in the script itself.

**Usage:**

At the completion of the script execution, you will receive a message similar to this:

```bash
Your RADKIt service is being enrolled. Here are your RADKit Service details:

Service ID: abcd-1234-wxyz
User: superadmin
Password: Mypa$$123
Port: 8081
```

To access your lab devices via RADKit, first we need to add the lab devices to the RADKit service.

Using [RADKit Network Console](https://radkit.cisco.com/docs/pages/client_network_console.html) client from your PC, access the service by entering the following commands:

```bash
login <your Cisco SSO>
service <service id> no-sr
```

Example:

<img width="1600" alt="image" src="https://github.com/tariqhab/CML_RemoteAccess/assets/29232922/5c43288e-7448-432f-a828-77dc559c838b">

Enable the port forwarding so you can open the RADKit Service admin page from your PC, using the following commands:

```bash
show inventory
port_forward start radkitservice 8081 9999
```

Example:

<img width="1600" alt="image" src="https://github.com/tariqhab/CML_RemoteAccess/assets/29232922/29a8f45d-3fbd-4341-b195-d06989ee3331">

Once the port forwarding is setup, here is how you can open the RADKit Service admin page using the port 9999. Once you are on that page, you can add the rest of your devices, so they are also accessible to you via RADKit Network Console and RADKit Client.

To login to the portal from your computer, go to <https://localhost:9999> and use the superadmin password that was printed at the end of the script execution.

<img width="1600" alt="image" src="https://github.com/tariqhab/CML_RemoteAccess/assets/29232922/5c954e57-6a48-43df-b1b8-f8b3868b5f3b">

<img width="1600" alt="image" src="https://github.com/tariqhab/CML_RemoteAccess/assets/29232922/0ce29193-f39f-45d5-8094-29e88418f367">


Here is a sample lab topology showing the three nodes, on the bottom right, that are automatically added by the script. Cpnmvert

<img width="1600" alt="image" src="https://github.com/tariqhab/CML_RemoteAccess/assets/29232922/d06c7a38-28e9-44d2-8974-828bc4175ad4">

Enjoy!
