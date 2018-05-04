# Auditor

## Introduction

This application enables **periodic auditing** of the linux shells in the IOS-XR container-based architecture by running **individual python applications in each individual environment in IOS-XR (across Active-Standby HA systems)**, i.e.:      
&nbsp;    
>*   XR-LXC     
>*   ADMIN-LXC   
>*   HOST    
  
&nbsp;    
&nbsp;  
**Functionally**, the individual python applications:    
&nbsp;   
>*  **Collect local data based on a YAML based user-config** provided during the build process 
>*  **Store accummulated data in the form of XML that is strictly validated against a user-defined XML schema**.
>*  **Send the accummulated XML data periodically to an external server over SSH** where it may be easily processed and visualized using any tools that can consume the XML schema and the data.

&nbsp;    
&nbsp;   
Further, the **application supports**:       
&nbsp;      

>1.  **Installation**: on a High-Availability (Active/Standby RP) system through a single command.  
>2.  **A clean uninstallation**  across the entire system through a single command.  
>3.  **Troubleshooting**:   **Dump filesystem view** - The ability to view the entire system's affected (user-defined in YAML file) system across active/standby RPs using a single command.  
>4.  **Troubleshooting**:   **Gather debug Data** - The ability to collect generated logs from all the environments (Active/Standby XR LXC, Admin LXC, HOST) and create a single tar ball using a single command.  
    
&nbsp;    
&nbsp;   
No SMUs needed, leverages the native app-hosting architecture in IOS-XR and the internal SSH-based access between different parts of the IOS-XR architecture - namely, XR-LXC, Admin-LXC and HOST of the active and/or Standby RPs to easily manage movement of data, logs and apps across the system.



&nbsp;    
&nbsp;
## User Story (Click to Expand)
  
&nbsp;    
<a href="https://raw.githubusercontent.com/akshshar/xr-auditor/master/images/user_story_auditor.png">![user-story](https://raw.githubusercontent.com/akshshar/xr-auditor/master/images/user_story_auditor.png)</a>


&nbsp;    
&nbsp;  
## IOS-XR architecture

For a quick refresher on the IOS-XR container based architecture, see the figure below:    
&nbsp;    
&nbsp;  

<a href="https://github.com/akshshar/xr-auditor/blob/master/images/IOS-XR-architecture.png?raw=true">![iosxr-architecture](https://github.com/akshshar/xr-auditor/blob/master/images/IOS-XR-architecture.png?raw=true)</a> . 

&nbsp;    
&nbsp;  

### IOS-XR AAA support vs Linux
As shown above, access to the linux shells (in blue inside the containers) and the underlying shells is protected through XR AAA authentication and authorization.
IOS-XR AAA also supports accounting which sends logs to a remote TACACS/RADIUS server to log what an authenticated and authorized user is upto on the XR interface.  

While IOS-XR supports the 3 A's of AAA (Authentication, Authorization and Accounting),  Linux supports only 2 of them: Authentication and authorization.  
Usually accounting is handled through separate tools such as auditd, snoopy etc. We showcase the usage of snoopy with IOS-XR here:  <https://github.com/akshshar/snoopy-xr>    

### IOS-XR Telemetry support vs Linux . 

Similarly, IOS-XR also supports sending structured operational data (modeled using Yang models) over transports such as gRPC, TCP and UDP to external receivers that can process the data - You can learn more about IOS-XR telemetry here:   
><https://xrdocs.github.io/telemetry/>   


Further, Linux doesn't really have a telemetry system by default - there are variety of solutions available that can provide structured data for various individual applications and files on the system, but none of them support a clean one step installation, collection and troubleshooting capabilities across container based architecture as shown above.  


### Enter xr-auditor 

This is where [xr-auditor](https://github.com/akshshar/xr-auditor) shines. It allows a user to specify their collection requirements through YAML files, build the application into single binary and deploy the auditors in each domain(container) of the system in a couple of steps.
  
  
xr-auditor is installed using a single binary generated out of the code in this git repo using pyinstaller. More details below. The installation involves running the binary on the XR-LXC shell of the Active RP:   

&nbsp;    
&nbsp;  

<a href="https://github.com/akshshar/xr-auditor/blob/master/images/iosxr-auditor-install.png?raw=true">![xr-auditor-install](https://github.com/akshshar/xr-auditor/blob/master/images/iosxr-auditor-install.png?raw=true)</a> . 


&nbsp;    
&nbsp;  

Once the install is triggered, individual cron jobs and apps are set up in the different domains as shown below to start sending collected data periodically to a remote server (identified in the SERVER_CONFIG in `userfiles/auditor.cfg.yml`) securely over SSH:  

&nbsp;    
&nbsp;  
  
<a href="https://github.com/akshshar/xr-auditor/blob/master/images/iosxr-auditor-operation.png?raw=true">![xr-auditor-install](https://github.com/akshshar/xr-auditor/blob/master/images/iosxr-auditor-operation.png?raw=true)</a> 

&nbsp;    
&nbsp;  



## Setting up the Build environment on your laptop:

All you need to build the application is a linux environment with python 2.7 installed.
To make things simpler, there is a vagrant setup already included with the code. We will use the vagrant setup to build and test our application against IOS-XRv64 on our laptops before we run it on physical hardware (NCS5500):

The vagrant setup looks something like this:  

<a href="https://raw.githubusercontent.com/akshshar/xr-auditor/master/images/vagrant_setup.png">![vagrant setup](https://raw.githubusercontent.com/akshshar/xr-auditor/master/images/vagrant_setup.png)</a>


>If you're not familiar with vagrant and associated workflows I would suggest first going through the following tutorials on [xrdocs](https://xrdocs.github.io/) before continuing (these tutorials will also show how to gain access to the IOS-XR vagrant box if you don't already have it):
>
>* [XR toolbox, Part 1 : IOS-XR Vagrant Quick Start](https://xrdocs.github.io/application-hosting/tutorials/iosxr-vagrant-quickstart)
>* [XR Toolbox, Part 2 : Bootstrap XR configuration with Vagrant](https://xrdocs.github.io/application-hosting/tutorials/iosxr-vagrant-bootstrap-config)
>* [https://xrdocs.github.io/application-hosting/tutorials/2016-06-06-xr-toolbox-app-development-topology](https://xrdocs.github.io/application-hosting/tutorials/2016-06-06-xr-toolbox-app-development-topology) . 
  
&nbsp;    
&nbsp; 

## Building the Application:
      
&nbsp;    
&nbsp;   
*  **Step 1**: Clone the [xr-auditor]() git repo:

   ```
   AKSHSHAR-M-33WP: akshshar$ git clone https://github.com/akshshar/xr-auditor.git
   Cloning into 'xr-auditor'...
   remote: Counting objects: 502, done.
   remote: Compressing objects: 100% (23/23), done.
   remote: Total 502 (delta 12), reused 4 (delta 1), pack-reused 478
   Receiving objects: 100% (502/502), 8.92 MiB | 4.19 MiB/s, done.
   Resolving deltas: 100% (317/317), done.
   AKSHSHAR-M-33WP: akshshar$ 
   AKSHSHAR-M-33WP: akshshar$ cd xr-auditor/
   AKSHSHAR-M-33WP:xr-auditor akshshar$ ls
   README.md		cleanup.sh		cron			requirements.txt	userfiles
   build_app.sh		core			images			specs			vagrant
   AKSHSHAR-M-33WP:xr-auditor akshshar$ 
   ```
     
&nbsp;    
&nbsp;     
*  **Step 2**: Drop into the `vagrant` directory and spin up the vagrant topology (shown above):

    >**Note**:  Make sure you've gone through the tutorial:  [XR toolbox, Part 1 : IOS-XR Vagrant Quick Start](https://xrdocs.github.io/application-hosting/tutorials/iosxr-vagrant-quickstart) and already have the `IOS-XRv` vagrant box on your system:  
   > ```
   > AKSHSHAR-M-33WP:~ akshshar$ vagrant box list
   > IOS-XRv            (virtualbox, 0)
   > AKSHSHAR-M-33WP:~ akshshar$ 
   > ```


    
    Now, in the vagrant directory, issue a `vagrant up`:
    
    ```
    AKSHSHAR-M-33WP:vagrant akshshar$ vagrant up
    Bringing machine 'rtr' up with 'virtualbox' provider...
    Bringing machine 'devbox' up with 'virtualbox' provider...
    ==> rtr: Importing base box 'IOS-XRv'...
    ==> rtr: Matching MAC address for NAT networking...
    ==> rtr: Setting the name of the VM: vagrant_rtr_1525415374584_85170
    ==> rtr: Clearing any previously set network interfaces...
    ==> rtr: Preparing network interfaces based on configuration...
        rtr: Adapter 1: nat
        rtr: Adapter 2: intnet
    ==> rtr: Forwarding ports...
        rtr: 57722 (guest) => 2222 (host) (adapter 1)
        rtr: 22 (guest) => 2223 (host) (adapter 1)
    ==> rtr: Running 'pre-boot' VM customizations...
    ==> rtr: Booting VM...
    
    
    
    .......
    
    
    
    devbox: Removing insecure key from the guest if it's present...
    devbox: Key inserted! Disconnecting and reconnecting using new SSH key... 
    ==> devbox: Machine booted and ready!
    ==> devbox: Checking for guest additions in VM...
    ==> devbox: Configuring and enabling network interfaces...
    ==> devbox: Mounting shared folders...
        devbox: /vagrant => /Users/akshshar/xr-auditor/vagrant
        
    ==> rtr: Machine 'rtr' has a post `vagrant up` message. This is a message
    ==> rtr: from the creator of the Vagrantfile, and not from Vagrant itself:
    ==> rtr: 
    ==> rtr: 
    ==> rtr:     Welcome to the IOS XRv (64-bit) VirtualBox.
    ==> rtr:     To connect to the XR Linux shell, use: 'vagrant ssh'.
    ==> rtr:     To ssh to the XR Console, use: 'vagrant port' (vagrant version > 1.8)
    ==> rtr:     to determine the port that maps to guestport 22,
    ==> rtr:     then: 'ssh vagrant@localhost -p <forwarded port>'
    ==> rtr: 
    ==> rtr:     IMPORTANT:  READ CAREFULLY
    ==> rtr:     The Software is subject to and governed by the terms and conditions
    ==> rtr:     of the End User License Agreement and the Supplemental End User
    ==> rtr:     License Agreement accompanying the product, made available at the
    ==> rtr:     time of your order, or posted on the Cisco website at
    ==> rtr:     www.cisco.com/go/terms (collectively, the 'Agreement').
    ==> rtr:     As set forth more fully in the Agreement, use of the Software is
    ==> rtr:     strictly limited to internal use in a non-production environment
    ==> rtr:     solely for demonstration and evaluation purposes. Downloading,
    ==> rtr:     installing, or using the Software constitutes acceptance of the
    ==> rtr:     Agreement, and you are binding yourself and the business entity
    ==> rtr:     that you represent to the Agreement. If you do not agree to all
    ==> rtr:     of the terms of the Agreement, then Cisco is unwilling to license
    ==> rtr:     the Software to you and (a) you may not download, install or use the
    ==> rtr:     Software, and (b) you may return the Software as more fully set forth
    ==> rtr:     in the Agreement.
    AKSHSHAR-M-33WP:vagrant akshshar$ 

    ```
    Once you see the above message, the devices should have booted up. You can check the status using `vagrant status`
    
    ```
    AKSHSHAR-M-33WP:vagrant akshshar$ vagrant status
    Current machine states:

    rtr                       running (virtualbox)
    devbox                    running (virtualbox)

    This environment represents multiple VMs. The VMs are all listed
    above with their current state. For more information about a specific
    VM, run `vagrant status NAME`.
    AKSHSHAR-M-33WP:vagrant akshshar$ 
    
    ```    
    
&nbsp;    
&nbsp;   
    
*  **Step 3**:  Note down the ports used for SSH (port 22) by the `rtr` and by `devbox`:

   ```
   AKSHSHAR-M-33WP:vagrant akshshar$ vagrant port rtr
   The forwarded ports for the machine are listed below. Please note that
   these values may differ from values configured in the Vagrantfile if the
   provider supports automatic port collision detection and resolution.

        22 (guest) => 2223 (host)
     57722 (guest) => 2222 (host)
   AKSHSHAR-M-33WP:vagrant akshshar$ 
   AKSHSHAR-M-33WP:vagrant akshshar$ 
   AKSHSHAR-M-33WP:vagrant akshshar$ vagrant port devbox
   The forwarded ports for the machine are listed below. Please note that
   these values may differ from values configured in the Vagrantfile if the
   provider supports automatic port collision detection and resolution.

        22 (guest) => 2200 (host)
    AKSHSHAR-M-33WP:vagrant akshshar$ 
    AKSHSHAR-M-33WP:vagrant akshshar$ 
    ```
    
&nbsp;    
&nbsp;       
*   **Step 4**:  SSH into the vagrant box (either by using `vagrant ssh devbox` or by using the port discovered above (2200 for devbox): `ssh -p 2200 vagrant@localhost`): 

    >Password is `vagrant`

    ```
    AKSHSHAR-M-33WP:vagrant akshshar$ ssh -p 2200 vagrant@localhost
    vagrant@localhost's password: 
    Welcome to Ubuntu 16.04.4 LTS (GNU/Linux 4.4.0-87-generic x86_64)

    * Documentation:  https://help.ubuntu.com
    * Management:     https://landscape.canonical.com
    * Support:        https://ubuntu.com/advantage

    0 packages can be updated.
    0 updates are security updates.
    
    Last login: Fri May  4 10:41:50 2018 from 10.0.2.2
    vagrant@vagrant:~$ 
    vagrant@vagrant:~$ 
    
    ```
    &nbsp;     
    
    Now again clone the xr-auditor app so that you have the application code available for build inside the devbox environment:  
    
    
    ```
    vagrant@vagrant:~$ git clone https://github.com/akshshar/xr-auditor.git
    Cloning into 'xr-auditor'...
    remote: Counting objects: 390, done.
    remote: Compressing objects: 100% (185/185), done.
    remote: Total 390 (delta 252), reused 333 (delta 195), pack-reused 0
    Receiving objects: 100% (390/390), 7.56 MiB | 3.51 MiB/s, done.
    Resolving deltas: 100% (252/252), done.
    Checking connectivity... done.
    vagrant@vagrant:~$ cd xr-auditor/
    vagrant@vagrant:~/xr-auditor$ 

    
    ```  
    
&nbsp;    
&nbsp;  

*  **Step 5**:   Create a new ssh-key pair for your devbox environment (if you see see the earlier [image]
(https://github.com/akshshar/xr-auditor/blob/master/images/iosxr-auditor-operation.png?raw=true) the devbox will serve as the remote server to which the router sends the collected XML data.

   >For password-less operation, the way we make this work is:  
   >    
   >1. Create an ssh-key pair on the server (devbox) .  
   > 
   >2. Add the public key of the pair to the devbox (server)'s  ~/.ssh/authorized_keys file . 
   > 
   >3. Package the private key as part of the app during the build process and transfer to the router .  
   >  
   >The app on the router then uses the private key to ssh and transfer files to the server (devbox) without requiring a password.   
    

   Following the above steps on devbox:    
    
    
   *  Create the ssh-key pair:  
    
    
      ```
      vagrant@vagrant:~/xr-auditor$ ssh-keygen -t rsa
      Generating public/private rsa key pair.
      Enter file in which to save the key (/home/vagrant/.ssh/id_rsa): 
      Enter passphrase (empty for no passphrase): 
      Enter same passphrase again: 
      Your identification has been saved in /home/vagrant/.ssh/id_rsa.
      Your public key has been saved in /home/vagrant/.ssh/id_rsa.pub.
      The key fingerprint is:
      SHA256:nUQqNANDpVUjwJLZ+7LrFY4go/y+yBcc+ProRqYejF8 vagrant@vagrant
      The key's randomart image is:
      +---[RSA 2048]----+
      |   *=+B.o .      |
      |  + o= + +       |
      |  ..... . .      |
      | . ..  . o .     |
      |o + ... S o      |
      |== =.o..         |
      |*+. Eoo          |
      |o+=o..           |
      |+*=*+.           |
      +----[SHA256]-----+
      vagrant@vagrant:~/xr-auditor$ 
      ```
    
    
   *  Add the public key to authorized_keys:
      
      ```
      vagrant@vagrant:~/xr-auditor$ 
      vagrant@vagrant:~/xr-auditor$ cat ~/.ssh/id_rsa >> ~/.ssh/authorized_keys 
      vagrant@vagrant:~/xr-auditor$ 
      ```
    
   *  Copy the private key to the folder `userfiles/` in the xr-auditor directory:
     
      ```
      vagrant@vagrant:~/xr-auditor$ 
      vagrant@vagrant:~/xr-auditor$ cp ~/.ssh/id_rsa userfiles/id_rsa_server 
      vagrant@vagrant:~/xr-auditor$ 
      ```
&nbsp;    
&nbsp;  

*   **Step 6**:  Edit the appropriate settings in the `userfiles/auditor.cfg.yml` file to match the environment you are building for. This file encapsulates information about the router, the server to which the data will be sent, the installation directories for the app and the compliance data that the app must collect. Follow the instructions specified in the yml file to fill everything out:

    <a href="https://github.com/akshshar/xr-auditor/blob/master/images/auditor_cfg_yml_edits.png?raw=true">![auditor_cfg_yml_edits](https://github.com/akshshar/xr-auditor/blob/master/images/auditor_cfg_yml_edits.png?raw=true)</a>



*  **Step 7**:  Now you're all ready to build the app. Eventually a single binary will be created as part of the build process  and this app will be called `auditor`.

   This app internally will consist of the following file structure:
   
   ```
   auditor
     |
     |--- userfiles
     |          |
     |          |---  audit.cfg.yml
     |          | 
     |          |---  compliance.xsd
     |          |
     |          |---  id_rsa_server
     |
     |
     |--- audit_xr.bin
     |          |
     |          |--- userfiles
     |          |        |
     |          |        |---  audit.cfg.yml
     |          |        |
     |          |        |---  compliance.xsd
     |          |        |
     |          |        |--- id_rsa_server
     |          |
     |          |
     |          |--- audit_xr.py
     |
     |
     |
     |--- audit_admin.bin
     |          |
     |          |--- userfiles
     |          |        |
     |          |        |--- audit.cfg.yml
     |          |        |
     |          |        |--- compliance.xsd
     |          |        |
     |          |        |--- id_rsa_server
     |          |
     |          |
     |          |--- audit_admin.py
     |
     |    
     |     
     |--- audit_host.bin
     |          |
     |          |--- userfiles
     |          |        |
     |          |        |--- audit.cfg.yml
     |          |        |
     |          |        |--- compliance.xsd
     |          |        |
     |          |        |--- id_rsa_server
     |          |
     |          |
     |          |--- audit_host.py
     |
     |
     |--- collector.bin
     |          |
     |          |--- userfiles
     |          |        |
     |          |        |--- audit.cfg.yml
     |          |        |
     |          |        |--- compliance.xsd
     |          |        |
     |          |        |--- id_rsa_server
     |          |
     |          |
     |          |--- collector.py
     |
     |
    
     ```
     
     
     
     To build the app, at the root of the git repo, issue the following command:
     (The `build_app.sh` shell script will automatically install the required dependencies, including pyinstaller, inside the devbox)
     
     ```
     vagrant@vagrant:~/xr-auditor$ 
     vagrant@vagrant:~/xr-auditor$ sudo -E ./build_app.sh 
     
     +++ which ./build_app.sh
     ++ dirname ./build_app.sh
     + SCRIPT_PATH=.
     + apt-get install -y git python-pip
     Reading package lists... Done
     Building dependency tree       
     Reading state information... Done
     git is already the newest version (1:2.7.4-0ubuntu1.3).
     python-pip is already the newest version (8.1.1-2ubuntu0.4).
     0 upgraded, 0 newly installed, 0 to remove and 0 not upgraded.
     + cd .
     + echo
     
     + [[ '' == '' ]]
     + pip install --upgrade pip==9.0.3
  
     ....
     
     + pyinstaller ./specs/xr.spec
     20 INFO: PyInstaller: 3.3.1
     20 INFO: Python: 2.7.12
     21 INFO: Platform: Linux-4.4.0-87-generic-x86_64-with-Ubuntu-16.04-xenial
     25 INFO: UPX is not available.
     26 INFO: Extending PYTHONPATH with paths
     ['/home/vagrant/xr-auditor/core', '/home/cisco/audit_xr_linux/specs']
     26 INFO: checking Analysis
     30 INFO: Appending 'datas' from .spec
     31 INFO: checking PYZ
     34 INFO: checking PKG
     34 INFO: Bootloader /usr/local/lib/python2.7/dist-packages/PyInstaller/bootloader/Linux-64bit/run
     35 INFO: checking EXE
     + pyinstaller ./specs/admin.spec
     20 INFO: PyInstaller: 3.3.1
     21 INFO: Python: 2.7.12
     21 INFO: Platform: Linux-4.4.0-87-generic-x86_64-with-Ubuntu-16.04-xenial
     24 INFO: UPX is not available.
     26 INFO: Extending PYTHONPATH with paths
     ['/home/vagrant/xr-auditor/core', '/home/cisco/audit_xr_linux/specs']
     26 INFO: checking Analysis
     30 INFO: Appending 'datas' from .spec
     30 INFO: checking PYZ
     33 INFO: checking PKG
     33 INFO: Bootloader /usr/local/lib/python2.7/dist-packages/PyInstaller/bootloader/Linux-64bit/run
     34 INFO: checking EXE
     + pyinstaller ./specs/host.spec
     20 INFO: PyInstaller: 3.3.1
     20 INFO: Python: 2.7.12
     21 INFO: Platform: Linux-4.4.0-87-generic-x86_64-with-Ubuntu-16.04-xenial
     24 INFO: UPX is not available.
     25 INFO: Extending PYTHONPATH with paths
     ['/home/vagrant/xr-auditor/core', '/home/cisco/audit_xr_linux/specs']
     25 INFO: checking Analysis
     
     .....
     
     
    67 INFO: running Analysis out00-Analysis.toc
    81 INFO: Caching module hooks...  
   83 INFO: Analyzing core/auditor.py
   1855 INFO: Processing pre-safe import module hook   _xmlplus
   1996 INFO: Processing pre-find module path hook   distutils
   2168 INFO: Loading module hooks...
   2169 INFO: Loading module hook "hook-distutils.py"...
   2170 INFO: Loading module hook "hook-xml.py"...
   2171 INFO: Loading module hook "hook-lxml.etree.py"...
   2178 INFO: Loading module hook "hook-httplib.py"...
   2179 INFO: Loading module hook "hook-encodings.py"...
   2500 INFO: Looking for ctypes DLLs
   2557 INFO: Analyzing run-time hooks ...
   2563 INFO: Looking for dynamic libraries
   2702 INFO: Looking for eggs
   2702 INFO: Python library not in binary dependencies. Doing additional searching...
   2722 INFO: Using Python library /usr/lib/x86_64-linux-gnu/libpython2.7.so.1.0
   2724 INFO: Warnings written to /home/vagrant/xr-auditor/build/auditor/warnauditor.txt
   2736 INFO: Graph cross-reference written to /home/vagrant/xr-auditor/build/auditor/xref-auditor.html
   2771 INFO: Appending 'datas' from .spec
   2773 INFO: checking PYZ
   2776 INFO: checking PKG
   2776 INFO: Building because /home/vagrant/xr-auditor/core/auditor.py changed
   2777 INFO: Building PKG (CArchive) out00-PKG.pkg
   6099 INFO: Building PKG (CArchive) out00-PKG.pkg completed successfully.
   6110 INFO: Bootloader /usr/local/lib/python2.7/dist-packages/PyInstaller/bootloader/Linux-64bit/run
   6111 INFO: checking EXE
   6113 INFO: Rebuilding out00-EXE.toc because pkg is more recent
   6114 INFO: Building EXE from out00-EXE.toc
   6119 INFO: Appending archive to ELF section in EXE /home/vagrant/xr-auditor/dist/auditor
   6172 INFO: Building EXE from out00-EXE.toc completed successfully.
   vagrant@vagrant:~/xr-auditor$
   ``` 
   
   At the end of the build, you will see the `auditor` binary appear inside a `dist/` directory at the root of the git repo:
   
   
   ```
   vagrant@vagrant:~/xr-auditor$ ls -lrt dist/
   total 61672
   -rwxr-xr-x 1 root root  7046744 May  4 10:43 audit_xr.bin
   -rwxr-xr-x 1 root root  7046848 May  4 10:43 audit_admin.bin
   -rwxr-xr-x 1 root root  7046616 May  4 10:43 audit_host.bin
   -rwxr-xr-x 1 root root  7049952 May  4 10:43 collector.bin
   -rwxr-xr-x 1 root root 34949880 May  4 10:49 auditor
   vagrant@vagrant:~/xr-auditor$ 
   ```
   
   
 ## Transfer auditor app to the router
 
 You will need the ssh credentials for your IOS-XR router to transfer the generated app to its `/misc/scratch` directory (also called `disk0:`.
 
 >In our **vagrant** setup, the credentials are `vagrant/vagrant`.
 > Note, 2223 is the port used by the vagrant IOS-XRv instance for its SSH session (See `vagrant port` output from earlier)
 
 ```
vagrant@vagrant:~/xr-auditor$ scp -P 2223 dist/auditor vagrant@10.0.2.2:/misc/scratch/
vagrant@10.0.2.2's password: 
auditor  

```


## Running the auditor app

You can easily run the following steps over SSH itself (in fact Ansible Playbooks will be used for this purpose, explained in the `/ansible` directory README.

For now, let's jump into the router and manually try out the options available:
> ssh is triggered from your laptop or the host on which `vagrant` is running

```
AKSHSHAR-M-33WP:vagrant akshshar$ 
AKSHSHAR-M-33WP:vagrant akshshar$ ssh -p 2223 vagrant@localhost
vagrant@localhost's password: 


RP/0/RP0/CPU0:ios#
RP/0/RP0/CPU0:ios#
RP/0/RP0/CPU0:ios#
RP/0/RP0/CPU0:ios#

```

###  View the options available

Jump into the bash shell in the IOS-XRv instance and use the `-h` option for the auditor app:


```
RP/0/RP0/CPU0:ios#
RP/0/RP0/CPU0:ios#
RP/0/RP0/CPU0:ios#bash
Fri May  4 15:28:45.654 UTC

[xr-vm_node0_RP0_CPU0:~]$
[xr-vm_node0_RP0_CPU0:~]$
xr-vm_node0_RP0_CPU0:~]$/misc/scratch/auditor -h
usage: auditor [-h] [-v] [-i] [-u] [-c] [-l] [-o TARFILE_OUTPUT_DIR] [-d]

optional arguments:
  -h, --help            show this help message and exit
  -v, --version         Display Current version of the Auditor app and exit
  -i, --install         Install the required artifacts (audit apps, collectors
                        and cron jobs) to default locations or to those
                        specified in auditor.cfg.yml
  -u, --uninstall       Uninstall all the artifacts from the system based on
                        auditor.cfg.yml settings
  -c, --clean-xml       Remove old XML files from the system
  -l, --list-files      List all the audit related files (apps, cron jobs, xml
                        files) currently on the system
  -o TARFILE_OUTPUT_DIR, --output-logs-to-dir TARFILE_OUTPUT_DIR
                        Specify the directory to use to collect the collated
                        logs from all nodes on the system
  -d, --debug           Enable verbose logging
[xr-vm_node0_RP0_CPU0:~]$
```



###  Dump Auditor Version 
  
Use the `-v` option:

```
RP/0/RP0/CPU0:ios#
RP/0/RP0/CPU0:ios#bash
Fri May  4 15:25:52.977 UTC

[xr-vm_node0_RP0_CPU0:~]$
[xr-vm_node0_RP0_CPU0:~]$
[xr-vm_node0_RP0_CPU0:~]$/misc/scratch/auditor -v
v1.0.0
[xr-vm_node0_RP0_CPU0:~]$

```


### Install all the auditing components:

Use the `-i` option:  


``
[xr-vm_node0_RP0_CPU0:~]$
[xr-vm_node0_RP0_CPU0:~]$/misc/scratch/auditor -i
2018-05-04 15:26:37,536 - DebugZTPLogger - INFO - Using root-lr user specified in auditor.cfg.yml, Username: vagrant
2018-05-04 15:26:37,545 - DebugZTPLogger - INFO - XR LXC audit app successfully copied
2018-05-04 15:26:37,550 - DebugZTPLogger - INFO - XR LXC audit cron job successfully set up
2018-05-04 15:26:40,012 - DebugZTPLogger - INFO - Admin LXC audit app successfully copied
2018-05-04 15:26:42,791 - DebugZTPLogger - INFO - Admin LXC audit cron file successfully copied and activated
2018-05-04 15:26:46,506 - DebugZTPLogger - INFO - HOST audit app successfully copied
2018-05-04 15:26:50,851 - DebugZTPLogger - INFO - Host audit cron file successfully copied and activated
2018-05-04 15:26:50,863 - DebugZTPLogger - INFO - Collector app successfully copied
2018-05-04 15:26:50,868 - DebugZTPLogger - INFO - Collector cron job successfully set up in XR LXC
2018-05-04 15:26:50,868 - DebugZTPLogger - INFO - Successfully set up artifacts, IOS-XR Linux auditing is now ON
[xr-vm_node0_RP0_CPU0:~]$
```  
     
     
