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
     |--- xr
     |    |
     |    |--- audit_xr.bin
     |    |         |
     |    |         |--- userfiles
     |    |         |        |
     |    |         |        |--- audit.cfg.yml
     |    |         |        |
     |    |         |        |--- compliance.xsd
     |    |         |        |
     |    |         |        |--- id_rsa_server
     |    |         |
     |    |         |
     |    |         |--- audit_xr.py
     |    | 
     |    |--- audit_xr.cron
     |    
     |
     |
     |--- admin
     |    |
     |    |--- audit_admin.bin
     |    |         |
     |    |         |--- userfiles
     |    |         |        |
     |    |         |        |--- audit.cfg.yml
     |    |         |        |
     |    |         |        |--- compliance.xsd
     |    |         |        |
     |    |         |        |--- id_rsa_server
     |    |         |
     |    |         |
     |    |         |--- audit_admin.py
     |    | 
     |    |--- audit_admin.cron
     |    
     |
     |
     |--- host
     |    |
     |    |--- audit_host.bin
     |    |         |
     |    |         |--- userfiles
     |    |         |        |
     |    |         |        |--- audit.cfg.yml
     |    |         |        |
     |    |         |        |--- compliance.xsd
     |    |         |        |
     |    |         |        |--- id_rsa_server
     |    |         |
     |    |         |
     |    |         |--- audit_xr.py
     |    | 
     |    |--- audit_host.cron
     |    
     |--- collector
     |    |
     |    |---collector.bin
     |    |         |
     |    |         |--- userfiles
     |    |         |        |
     |    |         |        |--- audit.cfg.yml
     |    |         |        |
     |    |         |        |--- compliance.xsd
     |    |         |        |
     |    |         |        |--- id_rsa_server
     |    |         |
     |    |         |
     |    |         |--- collector.py
     |    | 
     |    |--- collector.cron
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


RP/0/RP0/CPU0:rtr#
RP/0/RP0/CPU0:rtr#
RP/0/RP0/CPU0:rtr#
RP/0/RP0/CPU0:rtr#

```

###  View the options available

Jump into the bash shell in the IOS-XRv instance and use the `-h` option for the auditor app:


```
RP/0/RP0/CPU0:rtr#
RP/0/RP0/CPU0:rtr#
RP/0/RP0/CPU0:rtr#bash
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
RP/0/RP0/CPU0:rtr#
RP/0/RP0/CPU0:rtr#bash
Fri May  4 15:25:52.977 UTC

[xr-vm_node0_RP0_CPU0:~]$
[xr-vm_node0_RP0_CPU0:~]$
[xr-vm_node0_RP0_CPU0:~]$/misc/scratch/auditor -v
v1.0.0
[xr-vm_node0_RP0_CPU0:~]$

```


### Install all the auditing components:

Use the `-i` option to install the apps and cron jobs: 


```
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


The locations where the apps are installed and where the XML files get dumped are all defined in `userfiles/auditor.cfg.yml`. View the `INSTALLER_CONFIG` section of the yml file:  

<a href="https://github.com/akshshar/xr-auditor/blob/master/images/auditor_cfg_yml_installer_config.png?raw=true">![installer_config](https://github.com/akshshar/xr-auditor/blob/master/images/auditor_cfg_yml_installer_config.png?raw=true)</a>


These locations are used by the auditor app to install the `audit_xr.bin`, `collector.bin`, `audit_host.bin` and `audit_admin.bin` apps in the right directory and by the individual apps to determine where to generate and store the XML outputs.
The cron jobs get installed in `/etc/cron.d` of each location (XR, admin, host).
   
   

Use the `-l` option with the auditor app to dump the current state of all the relevant filesystems across active and standby RPs,  as defined by the `userfiles/auditor.cfg.yml` file :


```
[xr-vm_node0_RP0_CPU0:~]$
[xr-vm_node0_RP0_CPU0:~]$/misc/scratch/auditor -l
2018-05-04 16:03:28,841 - DebugZTPLogger - INFO - Using root-lr user specified in auditor.cfg.yml, Username: vagrant
2018-05-04 16:03:28,841 - DebugZTPLogger - INFO - 

####################################################
                       ACTIVE-RP XR                
#####################################################


2018-05-04 16:03:28,841 - DebugZTPLogger - INFO - 

###### App Directory ######

2018-05-04 16:03:28,846 - DebugZTPLogger - INFO - 
 /misc/scratch:

total 48172
drwxr-xr-x 2 root root     4096 Apr 24  2017 core
lrwxrwxrwx 1 root root       12 Apr 24  2017 config -> /misc/config
drwx------ 2 root root     4096 Apr 24  2017 clihistory
drwxr-xr-x 2 root root     4096 Apr 24  2017 crypto
-rw-r--r-- 1 root root     1549 May  4 06:32 status_file
drwxr-xr-x 8 root root     4096 May  4 06:32 ztp
drwxr-xr-x 2 root root     4096 May  4 07:27 nvgen_traces
-rwxr-xr-x 1 root root 34949880 May  4 10:49 auditor
-rw-r--r-- 1 root root      798 May  4 10:50 auditor_collated_logs.tar.gz
-rwx------ 1 root root  7049952 May  4 15:26 collector.bin
-rwx------ 1 root root  7046744 May  4 15:26 audit_xr.bin
-rwx------ 1 root root     1675 May  4 16:03 id_rsa
-rw-r--r-- 1 root root   240786 May  4 16:03 tpa.log

2018-05-04 16:03:28,846 - DebugZTPLogger - INFO - 

###### Cron directory ######

2018-05-04 16:03:28,851 - DebugZTPLogger - INFO - 
 /etc/cron.d:

total 12
-rw-r--r-- 1 root root 73 Apr 24  2017 logrotate.conf
-rw-r--r-- 1 root root 86 May  4 15:26 audit_cron_xr_2018-05-04_15-26-37
-rw-r--r-- 1 root root 87 May  4 15:26 audit_cron_collector_2018-05-04_15-26-50

2018-05-04 16:03:28,851 - DebugZTPLogger - INFO - 

###### XML Output Directory ######

2018-05-04 16:03:28,855 - DebugZTPLogger - INFO - 
 /misc/app_host:

total 84
drwx------ 2 root root 16384 Apr 24  2017 lost+found
drwxr-xr-x 5 root root  4096 Apr 24  2017 etc
drwxrwxr-x 2 root sudo  4096 Apr 24  2017 scratch
drwx-----x 9 root root  4096 Apr 24  2017 docker
drwxr-xr-x 5 root root  4096 Apr 24  2017 app_repo
srw-rw---- 1 root root     0 May  4 06:31 docker.sock
-rw-r--r-- 1 root root  8111 May  4 16:03 HOST.xml
-rw-r--r-- 1 root root  7908 May  4 16:03 ADMIN-LXC.xml
-rw-r--r-- 1 root root 23798 May  4 16:03 compliance_audit_rtr_11_1_1_10.xml
-rw-r--r-- 1 root root  8264 May  4 16:03 XR-LXC.xml

2018-05-04 16:03:28,855 - DebugZTPLogger - INFO - 

####################################################
                       ACTIVE-RP COLLECTOR                
#####################################################


2018-05-04 16:03:28,856 - DebugZTPLogger - INFO - 

###### App Directory ######

2018-05-04 16:03:28,860 - DebugZTPLogger - INFO - 
 /misc/scratch:

total 48172
drwxr-xr-x 2 root root     4096 Apr 24  2017 core
lrwxrwxrwx 1 root root       12 Apr 24  2017 config -> /misc/config
drwx------ 2 root root     4096 Apr 24  2017 clihistory
drwxr-xr-x 2 root root     4096 Apr 24  2017 crypto
-rw-r--r-- 1 root root     1549 May  4 06:32 status_file
drwxr-xr-x 8 root root     4096 May  4 06:32 ztp
drwxr-xr-x 2 root root     4096 May  4 07:27 nvgen_traces
-rwxr-xr-x 1 root root 34949880 May  4 10:49 auditor
-rw-r--r-- 1 root root      798 May  4 10:50 auditor_collated_logs.tar.gz
-rwx------ 1 root root  7049952 May  4 15:26 collector.bin
-rwx------ 1 root root  7046744 May  4 15:26 audit_xr.bin
-rwx------ 1 root root     1675 May  4 16:03 id_rsa
-rw-r--r-- 1 root root   240786 May  4 16:03 tpa.log

2018-05-04 16:03:28,860 - DebugZTPLogger - INFO - 

###### Cron directory ######

2018-05-04 16:03:28,866 - DebugZTPLogger - INFO - 
 /etc/cron.d:

total 12
-rw-r--r-- 1 root root 73 Apr 24  2017 logrotate.conf
-rw-r--r-- 1 root root 86 May  4 15:26 audit_cron_xr_2018-05-04_15-26-37
-rw-r--r-- 1 root root 87 May  4 15:26 audit_cron_collector_2018-05-04_15-26-50

2018-05-04 16:03:28,866 - DebugZTPLogger - INFO - 

###### XML Output Directory ######

2018-05-04 16:03:28,872 - DebugZTPLogger - INFO - 
 /misc/app_host:

total 84
drwx------ 2 root root 16384 Apr 24  2017 lost+found
drwxr-xr-x 5 root root  4096 Apr 24  2017 etc
drwxrwxr-x 2 root sudo  4096 Apr 24  2017 scratch
drwx-----x 9 root root  4096 Apr 24  2017 docker
drwxr-xr-x 5 root root  4096 Apr 24  2017 app_repo
srw-rw---- 1 root root     0 May  4 06:31 docker.sock
-rw-r--r-- 1 root root  8111 May  4 16:03 HOST.xml
-rw-r--r-- 1 root root  7908 May  4 16:03 ADMIN-LXC.xml
-rw-r--r-- 1 root root 23798 May  4 16:03 compliance_audit_rtr_11_1_1_10.xml
-rw-r--r-- 1 root root  8264 May  4 16:03 XR-LXC.xml

2018-05-04 16:03:28,872 - DebugZTPLogger - INFO - 

####################################################
                       ACTIVE-RP ADMIN                
#####################################################


2018-05-04 16:03:28,872 - DebugZTPLogger - INFO - 

###### App Directory ######

2018-05-04 16:03:29,460 - DebugZTPLogger - INFO - 
 /misc/scratch:

total 7164
drwxr-xr-x 2 root root    4096 Apr 24  2017 core
drwxr-xr-x 2 root root    4096 Apr 24  2017 shelf_mgr_pds
-rw-r--r-- 1 root root     579 May  4 06:31 card_specific_install
--wxr-s--- 1 root root   11974 May  4 06:31 calvados_log_tacacsd_0_0.out
--wxr-sr-- 1 root root    1822 May  4 06:31 calvados_log_instagt_log_0_0.out
--wxr-Sr-- 1 root root    3388 May  4 06:31 calvados_log_vmm_0_0.out
--wxr-sr-x 1 root root   28112 May  4 06:33 calvados_log_confd_helper_0_0.out
-rwx------ 1 root root 7046848 May  4 15:26 audit_admin.bin
-rw-r--r-- 1 root root    7908 May  4 16:03 ADMIN-LXC.xml
--wxr-Sr-x 1 root root  211763 May  4 16:03 calvados_log_aaad_0_0.out
2018-05-04 16:03:29,460 - DebugZTPLogger - INFO - 

###### Cron directory ######

2018-05-04 16:03:30,075 - DebugZTPLogger - INFO - 
 /etc/cron.d:

total 8
-rw-r--r-- 1 root root 73 Apr 24  2017 logrotate.conf
-rw-r--r-- 1 root root 89 May  4 15:26 audit_cron_admin_2018-05-04_15-26-40
2018-05-04 16:03:30,076 - DebugZTPLogger - INFO - 

###### XML Output Directory ######

2018-05-04 16:03:30,639 - DebugZTPLogger - INFO - 
 /misc/scratch:

total 7168
drwxr-xr-x 2 root root    4096 Apr 24  2017 core
drwxr-xr-x 2 root root    4096 Apr 24  2017 shelf_mgr_pds
-rw-r--r-- 1 root root     579 May  4 06:31 card_specific_install
--wxr-s--- 1 root root   11974 May  4 06:31 calvados_log_tacacsd_0_0.out
--wxr-sr-- 1 root root    1822 May  4 06:31 calvados_log_instagt_log_0_0.out
--wxr-Sr-- 1 root root    3388 May  4 06:31 calvados_log_vmm_0_0.out
--wxr-sr-x 1 root root   28112 May  4 06:33 calvados_log_confd_helper_0_0.out
-rwx------ 1 root root 7046848 May  4 15:26 audit_admin.bin
-rw-r--r-- 1 root root    7908 May  4 16:03 ADMIN-LXC.xml
--wxr-Sr-x 1 root root  215191 May  4 16:03 calvados_log_aaad_0_0.out
2018-05-04 16:03:30,640 - DebugZTPLogger - INFO - 

####################################################
                       ACTIVE-RP HOST                
#####################################################


2018-05-04 16:03:30,640 - DebugZTPLogger - INFO - 

###### App Directory ######

2018-05-04 16:03:31,334 - DebugZTPLogger - INFO - 
 /misc/scratch:

total 6888
drwxr-xr-x 2 root root    4096 Apr 24  2017 core
-rwx------ 1 root root 7046616 May  4 15:26 audit_host.bin
2018-05-04 16:03:31,334 - DebugZTPLogger - INFO - 

###### Cron directory ######

2018-05-04 16:03:32,063 - DebugZTPLogger - INFO - 
 /etc/cron.d:

total 8
-rw-r--r-- 1 root root 73 Apr 24  2017 logrotate.conf
-rw-r--r-- 1 root root 88 May  4 15:26 audit_cron_host_2018-05-04_15-26-46
2018-05-04 16:03:32,064 - DebugZTPLogger - INFO - 

###### XML Output Directory ######

2018-05-04 16:03:32,788 - DebugZTPLogger - INFO - 
 /misc/app_host:

total 84
drwx------ 2 root root 16384 Apr 24  2017 lost+found
drwxr-xr-x 5 root root  4096 Apr 24  2017 etc
drwxrwxr-x 2 root sudo  4096 Apr 24  2017 scratch
drwx-----x 9 root root  4096 Apr 24  2017 docker
drwxr-xr-x 5 root root  4096 Apr 24  2017 app_repo
srw-rw---- 1 root root     0 May  4 06:31 docker.sock
-rw-r--r-- 1 root root  8111 May  4 16:03 HOST.xml
-rw-r--r-- 1 root root  7908 May  4 16:03 ADMIN-LXC.xml
-rw-r--r-- 1 root root 23798 May  4 16:03 compliance_audit_rtr_11_1_1_10.xml
-rw-r--r-- 1 root root  8264 May  4 16:03 XR-LXC.xml
[xr-vm_node0_RP0_CPU0:~]$


```


### list the generated XML files

You will see the generated XML files in the directories specified in the `userfiles/auditor.cfg.yml` files as explained in the previous section. The recommendation is to set the `output_xml_dir` for both XR and collector to `/misc/app_host` to view all the XML files in one location, but it is not mandatory.  


```
[xr-vm_node0_RP0_CPU0:~]$
[xr-vm_node0_RP0_CPU0:~]$ls -lrt /misc/app_host/
total 84
drwx------ 2 root root 16384 Apr 24  2017 lost+found
drwxr-xr-x 5 root root  4096 Apr 24  2017 etc
drwxrwxr-x 2 root sudo  4096 Apr 24  2017 scratch
drwx-----x 9 root root  4096 Apr 24  2017 docker
drwxr-xr-x 5 root root  4096 Apr 24  2017 app_repo
srw-rw---- 1 root root     0 May  4 06:31 docker.sock
-rw-r--r-- 1 root root  7908 May  4 16:05 ADMIN-LXC.xml
-rw-r--r-- 1 root root  8111 May  4 16:05 HOST.xml
-rw-r--r-- 1 root root 23799 May  4 16:05 compliance_audit_rtr_11_1_1_10.xml
-rw-r--r-- 1 root root  8264 May  4 16:05 XR-LXC.xml
[xr-vm_node0_RP0_CPU0:~]$



```

Here,
`-rw-r--r-- 1 root root  7908 May  4 16:05 ADMIN-LXC.xml`  is generated by audit_admin.bin running in the Admin LXC
`-rw-r--r-- 1 root root  8111 May  4 16:05 HOST.xml` is generated by audit_host.bin running in the Host shell
`-rw-r--r-- 1 root root  8264 May  4 16:05 XR-LXC.xml` is generated by audit_xr.bin running in the XR shell
`-rw-r--r-- 1 root root 23799 May  4 16:05 compliance_audit_rtr_11_1_1_10.xml` is generated by the collector app running in the XR shell.



### View the generated XML content on the Server


As specified earlier, the XML content generated by the collector app is transferred over SSH to the remote server, based on the SERVER_CONFIG settings in `userfiles/auditor.cfg.yml`:

So log back into devbox(server) and drop into the directory that you specified as `REMOTE_DIRECTORY` in `userfiles/auditor.cfg.yml`.

```
    # Specify the remote directory on the server
    # where the compliance XML file should be copied

    REMOTE_DIRECTORY: "/home/vagrant"

```

In this case, it is set to `/home/vagrant` so checking there:

```
AKSHSHAR-M-33WP:vagrant akshshar$ 
AKSHSHAR-M-33WP:vagrant akshshar$ vagrant ssh devbox
vagrant@127.0.0.1's password: 
Welcome to Ubuntu 16.04.4 LTS (GNU/Linux 4.4.0-87-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/advantage

0 packages can be updated.
0 updates are security updates.


Last login: Fri May  4 16:13:51 2018 from 10.0.2.2
vagrant@vagrant:~$ 
vagrant@vagrant:~$ 
vagrant@vagrant:~$ ls -lrt /misc/app
ls: cannot access '/misc/app': No such file or directory
vagrant@vagrant:~$ ls -lrt /home/vagrant/
total 28
drwxrwxr-x 10 vagrant vagrant  4096 May  4 10:42 xr-auditor
-rw-rw-r--  1 vagrant vagrant 23799 May  4 16:14 compliance_audit_rtr_11_1_1_10.xml
vagrant@vagrant:~$ 
vagrant@vagrant:~$ 
```

>Great! We see the xml file appear on the server, transmitted by the collector app.

Let's dump the content:

```
vagrant@vagrant:~$ cat compliance_audit_rtr_11_1_1_10.xml 
<?xml version="1.0" encoding="utf-8"?>
<COMPLIANCE-DUMP xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="1.0.0" xsi:noNamespaceSchemaLocation="compliance.xsd">
	<GENERAL>
		<PRODUCT>XRV-P-L--CH</PRODUCT>
		<VENDOR>Cisco</VENDOR>
		<IPADDR>11.1.1.10/24</IPADDR>
		<HOST>rtr</HOST>
		<VERSION>6.1.2</VERSION>
		<DATE>20180504-16:14 UTC</DATE>
		<OS>IOS-XR</OS>
	</GENERAL>
	<INTEGRITY-SET>
		<INTEGRITY domain="XR-LXC">
			<FILES>
				<FILE>
					<CONTENT>["#\t$OpenBSD: sshd_config,v 1.80 2008/07/02 02:24:18 djm Exp $", "# This is the sshd server system-wide configuration file.  See", "# sshd_config(5) for more information.", "# This sshd was compiled with PATH=/usr/bin:/bin:/usr/sbin:/sbin", "# The strategy used for options in the default sshd_config shipped with", "# OpenSSH is to specify options with their default value where", "# possible, but leave them commented.  Uncommented options change a", "# default value.", "#Port 22", "AddressFamily inet", "#ListenAddress 0.0.0.0", "#ListenAddress ::", "# Disable legacy (protocol version 1) support in the server for new", "# installations. In future the default will change to require explicit", "# activation of protocol 1", "Protocol 2", "# HostKey for protocol version 1", "#HostKey /etc/ssh/ssh_host_key", "# HostKeys for protocol version 2", "#HostKey /etc/ssh/ssh_host_rsa_key", "#HostKey /etc/ssh/ssh_host_dsa_key", "# Lifetime and size of ephemeral version 1 server key", "#KeyRegenerationInterval 1h", "#ServerKeyBits 1024", "# Logging", "# obsoletes QuietMode and FascistLogging", "#SyslogFacility AUTH", "#LogLevel INFO", "# Authentication:", "#LoginGraceTime 2m", "PermitRootLogin yes", "#StrictModes yes", "#MaxAuthTries 6", "#MaxSessions 10", "#RSAAuthentication yes", "#PubkeyAuthentication yes", "#AuthorizedKeysFile\t.ssh/authorized_keys", "# For this to work you will also need host keys in /etc/ssh/ssh_known_hosts", "#RhostsRSAAuthentication no", "# similar for protocol version 2", "#HostbasedAuthentication no", "# Change to yes if you don't trust ~/.ssh/known_hosts for", "# RhostsRSAAuthentication and HostbasedAuthentication", "#IgnoreUserKnownHosts no", "# Don't read the user's ~/.rhosts and ~/.shosts files", "#IgnoreRhosts yes", "# To disable tunneled clear text passwords, change to no here!", "#PasswordAuthentication yes", "PermitEmptyPasswords yes", "# Change to no to disable s/key passwords", "#ChallengeResponseAuthentication yes", "# Kerberos options", "#KerberosAuthentication no", "#KerberosOrLocalPasswd yes", "#KerberosTicketCleanup yes", "#KerberosGetAFSToken no", "# GSSAPI options", "#GSSAPIAuthentication no", "#GSSAPICleanupCredentials yes", "# Set this to 'yes' to enable PAM authentication, account processing,", "# and session processing. If this is enabled, PAM authentication will", "# be allowed through the ChallengeResponseAuthentication and", "# PasswordAuthentication.  Depending on your PAM configuration,", "# PAM authentication via ChallengeResponseAuthentication may bypass", "# the setting of \"PermitRootLogin without-password\".", "# If you just want the PAM account and session checks to run without", "# PAM authentication, then enable this but set PasswordAuthentication", "# and ChallengeResponseAuthentication to 'no'.", "#UsePAM no", "#AllowAgentForwarding yes", "#AllowTcpForwarding yes", "#GatewayPorts no", "#X11Forwarding no", "#X11DisplayOffset 10", "#X11UseLocalhost yes", "#PrintMotd yes", "#PrintLastLog yes", "#TCPKeepAlive yes", "#UseLogin no", "UsePrivilegeSeparation no", "#PermitUserEnvironment no", "Compression no", "ClientAliveInterval 15", "ClientAliveCountMax 4", "UseDNS no", "#PidFile /var/run/sshd.pid", "#MaxStartups 10", "#PermitTunnel no", "#ChrootDirectory none", "# no default banner path", "#Banner none", "# override default of no subsystems", "Subsystem\tsftp\t/usr/lib64/openssh/sftp-server", "# Example of overriding settings on a per-user basis", "#Match User anoncvs", "#\tX11Forwarding no", "#\tAllowTcpForwarding no", "#\tForceCommand cvs server"]</CONTENT>
					<CHECKSUM>97884b5c2cb2b75022c4b440ddc4245a</CHECKSUM>
					<CMD-LIST>
						<CMD>
							<REQUEST>ls -la</REQUEST>
							<RESPONSE>-rwxr-xr-x 1 root root 3275 Apr 24  2017 /etc/ssh/sshd_config</RESPONSE>
						</CMD>
					</CMD-LIST>
					<NAME>/etc/ssh/sshd_config</NAME>
				</FILE>
				<FILE>
					<CONTENT>["root:x:0:0:root:/root:/bin/sh", "daemon:x:1:1:daemon:/usr/sbin:/bin/sh", "bin:x:2:2:bin:/bin:/bin/sh", "sys:x:3:3:sys:/dev:/bin/sh", "sync:x:4:65534:sync:/bin:/bin/sync", "games:x:5:60:games:/usr/games:/bin/sh", "man:x:6:12:man:/var/cache/man:/bin/sh", "lp:x:7:7:lp:/var/spool/lpd:/bin/sh", "mail:x:8:8:mail:/var/mail:/bin/sh", "news:x:9:9:news:/var/spool/news:/bin/sh", "uucp:x:10:10:uucp:/var/spool/uucp:/bin/sh", "proxy:x:13:13:proxy:/bin:/bin/sh", "www-data:x:33:33:www-data:/var/www:/bin/sh", "backup:x:34:34:backup:/var/backups:/bin/sh", "list:x:38:38:Mailing List Manager:/var/list:/bin/sh", "irc:x:39:39:ircd:/var/run/ircd:/bin/sh", "gnats:x:41:41:Gnats Bug-Reporting System (admin):/var/lib/gnats:/bin/sh", "nobody:x:65534:65534:nobody:/nonexistent:/bin/sh", "messagebus:x:999:998::/var/lib/dbus:/bin/false", "rpc:x:998:996::/:/bin/false", "sshd:x:997:995::/var/run/sshd:/bin/false", "vagrant:x:1000:1009::/home/vagrant:/bin/sh"]</CONTENT>
					<CHECKSUM>0cabf9f93101d6876bba590e48bfda5e</CHECKSUM>
					<CMD-LIST>
						<CMD>
							<REQUEST>ls -la</REQUEST>
							<RESPONSE>-rw-r--r-- 1 root root 874 Apr 24  2017 /etc/passwd</RESPONSE>
						</CMD>
					</CMD-LIST>
					<NAME>/etc/passwd</NAME>
				</FILE>
				<FILE>
					<CHECKSUM>7ea587858977ef205c6a7419463359f7</CHECKSUM>
					<CMD-LIST>
						<CMD>
							<REQUEST>ls -la</REQUEST>
							<RESPONSE>lrwxrwxrwx 1 root root 7 Apr 24  2017 /usr/bin/python -&gt; python2</RESPONSE>
						</CMD>
					</CMD-LIST>
					<NAME>/usr/bin/python</NAME>
				</FILE>
				<FILE>
					<CONTENT>["# Defaults for dhcp initscript", "# sourced by /etc/init.d/dhcp-server", "# installed at /etc/default/dhcp-server by the maintainer scripts", "# On what interfaces should the DHCP server (dhcpd) serve DHCP requests?", "#       Separate multiple interfaces with spaces, e.g. \"eth0 eth1\".", "INTERFACES=\"\""]</CONTENT>
					<CHECKSUM>1c905007d96a8b16c58454b6da8cfd86</CHECKSUM>
					<CMD-LIST>
						<CMD>
							<REQUEST>ls -lhrt</REQUEST>
							<RESPONSE>-rw-r--r-- 1 root root 290 Apr 24  2017 /etc/default/dhcp-server</RESPONSE>
						</CMD>
					</CMD-LIST>
					<NAME>/etc/default/dhcp-server</NAME>
				</FILE>
			</FILES>
			<DIRECTORIES>
				<DIRECTORY>
					<CMD-LIST>
						<CMD>
							<REQUEST>ls -ld</REQUEST>
							<RESPONSE>drwxr-xr-x 3 root root 20480 Apr 24  2017 /usr/bin</RESPONSE>
						</CMD>
					</CMD-LIST>
					<NAME>/usr/bin</NAME>
				</DIRECTORY>
				<DIRECTORY>
					<CMD-LIST>
						<CMD>
							<REQUEST>ls -lrt</REQUEST>
							<RESPONSE>total 8
-rwx------ 1 root root   0 Apr 24  2017 log.txt
-rwx------ 1 root root  13 Apr 24  2017 card_instances.txt
-rw-r--r-- 1 root root 218 Apr 24  2017 cmdline
-rw-r--r-- 1 root root   0 May  4 16:13 test.txt</RESPONSE>
						</CMD>
						<CMD>
							<REQUEST>touch test.txt</REQUEST>
							<RESPONSE></RESPONSE>
						</CMD>
					</CMD-LIST>
					<NAME>/root</NAME>
				</DIRECTORY>
				<DIRECTORY>
					<CMD-LIST>
						<CMD>
							<REQUEST>ls -ld</REQUEST>
							<RESPONSE>drwxr-xr-x 7 root root 4096 May  4 15:26 /misc/scratch</RESPONSE>
						</CMD>
					</CMD-LIST>
					<NAME>/misc/scratch</NAME>
				</DIRECTORY>
				<DIRECTORY>
					<CMD-LIST>
						<CMD>
							<REQUEST>ls -ld</REQUEST>
							<RESPONSE>drwxr-xr-x 7 root root 4096 May  4 16:03 /misc/app_host</RESPONSE>
						</CMD>
					</CMD-LIST>
					<NAME>/misc/app_host</NAME>
				</DIRECTORY>
				<DIRECTORY>
					<CMD-LIST>
						<CMD>
							<REQUEST>ls -ld</REQUEST>
							<RESPONSE>drwxr-xr-x 57 root root 4096 May  4 06:32 /etc</RESPONSE>
						</CMD>
					</CMD-LIST>
					<NAME>/etc</NAME>
				</DIRECTORY>
				<DIRECTORY>
					<CMD-LIST>
						<CMD>
							<REQUEST>ls -ld</REQUEST>
							<RESPONSE>drwxr-xr-x 34 root root 4096 May  4 10:52 /</RESPONSE>
						</CMD>
					</CMD-LIST>
					<NAME>/</NAME>
				</DIRECTORY>
			</DIRECTORIES>
		</INTEGRITY>
		<INTEGRITY domain="ADMIN-LXC">
			<FILES>
				<FILE>
					<CONTENT>["#\t$OpenBSD: sshd_config,v 1.80 2008/07/02 02:24:18 djm Exp $", "# This is the sshd server system-wide configuration file.  See", "# sshd_config(5) for more information.", "# This sshd was compiled with PATH=/usr/bin:/bin:/usr/sbin:/sbin", "# The strategy used for options in the default sshd_config shipped with", "# OpenSSH is to specify options with their default value where", "# possible, but leave them commented.  Uncommented options change a", "# default value.", "#Port 22", "AddressFamily inet", "#ListenAddress 0.0.0.0", "#ListenAddress ::", "# Disable legacy (protocol version 1) support in the server for new", "# installations. In future the default will change to require explicit", "# activation of protocol 1", "Protocol 2", "# HostKey for protocol version 1", "#HostKey /etc/ssh/ssh_host_key", "# HostKeys for protocol version 2", "#HostKey /etc/ssh/ssh_host_rsa_key", "#HostKey /etc/ssh/ssh_host_dsa_key", "# Lifetime and size of ephemeral version 1 server key", "#KeyRegenerationInterval 1h", "#ServerKeyBits 1024", "# Logging", "# obsoletes QuietMode and FascistLogging", "#SyslogFacility AUTH", "#LogLevel INFO", "# Authentication:", "#LoginGraceTime 2m", "PermitRootLogin yes", "#StrictModes yes", "#MaxAuthTries 6", "#MaxSessions 10", "#RSAAuthentication yes", "#PubkeyAuthentication yes", "#AuthorizedKeysFile\t.ssh/authorized_keys", "# For this to work you will also need host keys in /etc/ssh/ssh_known_hosts", "#RhostsRSAAuthentication no", "# similar for protocol version 2", "#HostbasedAuthentication no", "# Change to yes if you don't trust ~/.ssh/known_hosts for", "# RhostsRSAAuthentication and HostbasedAuthentication", "#IgnoreUserKnownHosts no", "# Don't read the user's ~/.rhosts and ~/.shosts files", "#IgnoreRhosts yes", "# To disable tunneled clear text passwords, change to no here!", "#PasswordAuthentication yes", "PermitEmptyPasswords yes", "# Change to no to disable s/key passwords", "#ChallengeResponseAuthentication yes", "# Kerberos options", "#KerberosAuthentication no", "#KerberosOrLocalPasswd yes", "#KerberosTicketCleanup yes", "#KerberosGetAFSToken no", "# GSSAPI options", "#GSSAPIAuthentication no", "#GSSAPICleanupCredentials yes", "# Set this to 'yes' to enable PAM authentication, account processing,", "# and session processing. If this is enabled, PAM authentication will", "# be allowed through the ChallengeResponseAuthentication and", "# PasswordAuthentication.  Depending on your PAM configuration,", "# PAM authentication via ChallengeResponseAuthentication may bypass", "# the setting of \"PermitRootLogin without-password\".", "# If you just want the PAM account and session checks to run without", "# PAM authentication, then enable this but set PasswordAuthentication", "# and ChallengeResponseAuthentication to 'no'.", "#UsePAM no", "#AllowAgentForwarding yes", "#AllowTcpForwarding yes", "#GatewayPorts no", "#X11Forwarding no", "#X11DisplayOffset 10", "#X11UseLocalhost yes", "#PrintMotd yes", "#PrintLastLog yes", "#TCPKeepAlive yes", "#UseLogin no", "UsePrivilegeSeparation no", "#PermitUserEnvironment no", "Compression no", "ClientAliveInterval 15", "ClientAliveCountMax 4", "UseDNS no", "#PidFile /var/run/sshd.pid", "#MaxStartups 10", "#PermitTunnel no", "#ChrootDirectory none", "# no default banner path", "#Banner none", "# override default of no subsystems", "Subsystem\tsftp\t/usr/lib64/openssh/sftp-server", "# Example of overriding settings on a per-user basis", "#Match User anoncvs", "#\tX11Forwarding no", "#\tAllowTcpForwarding no", "#\tForceCommand cvs server"]</CONTENT>
					<CHECKSUM>97884b5c2cb2b75022c4b440ddc4245a</CHECKSUM>
					<CMD-LIST>
						<CMD>
							<REQUEST>ls -la</REQUEST>
							<RESPONSE>-rwxr-xr-x 1 root root 3275 Apr 24  2017 /etc/ssh/sshd_config</RESPONSE>
						</CMD>
					</CMD-LIST>
					<NAME>/etc/ssh/sshd_config</NAME>
				</FILE>
				<FILE>
					<CONTENT>["root:x:0:0:root:/root:/bin/sh", "daemon:x:1:1:daemon:/usr/sbin:/bin/sh", "bin:x:2:2:bin:/bin:/bin/sh", "sys:x:3:3:sys:/dev:/bin/sh", "sync:x:4:65534:sync:/bin:/bin/sync", "games:x:5:60:games:/usr/games:/bin/sh", "man:x:6:12:man:/var/cache/man:/bin/sh", "lp:x:7:7:lp:/var/spool/lpd:/bin/sh", "mail:x:8:8:mail:/var/mail:/bin/sh", "news:x:9:9:news:/var/spool/news:/bin/sh", "uucp:x:10:10:uucp:/var/spool/uucp:/bin/sh", "proxy:x:13:13:proxy:/bin:/bin/sh", "www-data:x:33:33:www-data:/var/www:/bin/sh", "backup:x:34:34:backup:/var/backups:/bin/sh", "list:x:38:38:Mailing List Manager:/var/list:/bin/sh", "irc:x:39:39:ircd:/var/run/ircd:/bin/sh", "gnats:x:41:41:Gnats Bug-Reporting System (admin):/var/lib/gnats:/bin/sh", "nobody:x:65534:65534:nobody:/nonexistent:/bin/sh", "messagebus:x:999:998::/var/lib/dbus:/bin/false", "rpc:x:998:996::/:/bin/false", "sshd:x:997:995::/var/run/sshd:/bin/false"]</CONTENT>
					<CHECKSUM>591fb16f798d29aa9dab2db5557ff4f8</CHECKSUM>
					<CMD-LIST>
						<CMD>
							<REQUEST>ls -la</REQUEST>
							<RESPONSE>-rw-r--r-- 1 root root 831 Apr 24  2017 /etc/passwd</RESPONSE>
						</CMD>
					</CMD-LIST>
					<NAME>/etc/passwd</NAME>
				</FILE>
				<FILE>
					<CHECKSUM>7ea587858977ef205c6a7419463359f7</CHECKSUM>
					<CMD-LIST>
						<CMD>
							<REQUEST>ls -la</REQUEST>
							<RESPONSE>lrwxrwxrwx 1 root root 7 Apr 24  2017 /usr/bin/python -&gt; python2</RESPONSE>
						</CMD>
					</CMD-LIST>
					<NAME>/usr/bin/python</NAME>
				</FILE>
				<FILE>
					<CONTENT>["# Defaults for dhcp initscript", "# sourced by /etc/init.d/dhcp-server", "# installed at /etc/default/dhcp-server by the maintainer scripts", "# On what interfaces should the DHCP server (dhcpd) serve DHCP requests?", "#       Separate multiple interfaces with spaces, e.g. \"eth0 eth1\".", "INTERFACES=\"\""]</CONTENT>
					<CHECKSUM>1c905007d96a8b16c58454b6da8cfd86</CHECKSUM>
					<CMD-LIST>
						<CMD>
							<REQUEST>ls -lhrt</REQUEST>
							<RESPONSE>-rw-r--r-- 1 root root 290 Apr 24  2017 /etc/default/dhcp-server</RESPONSE>
						</CMD>
					</CMD-LIST>
					<NAME>/etc/default/dhcp-server</NAME>
				</FILE>
			</FILES>
			<DIRECTORIES>
				<DIRECTORY>
					<CMD-LIST>
						<CMD>
							<REQUEST>ls -ld</REQUEST>
							<RESPONSE>drwxr-sr-x 3 root root 20480 Apr 24  2017 /usr/bin</RESPONSE>
						</CMD>
					</CMD-LIST>
					<NAME>/usr/bin</NAME>
				</DIRECTORY>
				<DIRECTORY>
					<CMD-LIST>
						<CMD>
							<REQUEST>ls -lrt</REQUEST>
							<RESPONSE>total 4
-rwx------ 1 root root   0 Apr 24  2017 calv_setup_ldpath.log
-rw-r--r-- 1 root root 227 Apr 24  2017 cmdline
-rw-r--r-- 1 root root   0 May  4 16:14 test.txt</RESPONSE>
						</CMD>
						<CMD>
							<REQUEST>touch test.txt</REQUEST>
							<RESPONSE></RESPONSE>
						</CMD>
					</CMD-LIST>
					<NAME>/root</NAME>
				</DIRECTORY>
				<DIRECTORY>
					<CMD-LIST>
						<CMD>
							<REQUEST>ls -ld</REQUEST>
							<RESPONSE>drwxr-xr-x 4 root root 4096 May  4 15:27 /misc/scratch</RESPONSE>
						</CMD>
					</CMD-LIST>
					<NAME>/misc/scratch</NAME>
				</DIRECTORY>
				<DIRECTORY>
					<CMD-LIST>
						<CMD>
							<REQUEST>ls -ld</REQUEST>
							<RESPONSE></RESPONSE>
						</CMD>
					</CMD-LIST>
					<NAME>/misc/app_host</NAME>
				</DIRECTORY>
				<DIRECTORY>
					<CMD-LIST>
						<CMD>
							<REQUEST>ls -ld</REQUEST>
							<RESPONSE>drwxr-sr-x 55 root root 4096 May  4 06:32 /etc</RESPONSE>
						</CMD>
					</CMD-LIST>
					<NAME>/etc</NAME>
				</DIRECTORY>
				<DIRECTORY>
					<CMD-LIST>
						<CMD>
							<REQUEST>ls -ld</REQUEST>
							<RESPONSE>drwxr-sr-x 28 root root 4096 May  4 06:30 /</RESPONSE>
						</CMD>
					</CMD-LIST>
					<NAME>/</NAME>
				</DIRECTORY>
			</DIRECTORIES>
		</INTEGRITY>
		<INTEGRITY domain="HOST">
			<FILES>
				<FILE>
					<CONTENT>["#\t$OpenBSD: sshd_config,v 1.80 2008/07/02 02:24:18 djm Exp $", "# This is the sshd server system-wide configuration file.  See", "# sshd_config(5) for more information.", "# This sshd was compiled with PATH=/usr/bin:/bin:/usr/sbin:/sbin", "# The strategy used for options in the default sshd_config shipped with", "# OpenSSH is to specify options with their default value where", "# possible, but leave them commented.  Uncommented options change a", "# default value.", "#Port 22", "AddressFamily inet", "#ListenAddress 0.0.0.0", "#ListenAddress ::", "# Disable legacy (protocol version 1) support in the server for new", "# installations. In future the default will change to require explicit", "# activation of protocol 1", "Protocol 2", "# HostKey for protocol version 1", "#HostKey /etc/ssh/ssh_host_key", "# HostKeys for protocol version 2", "#HostKey /etc/ssh/ssh_host_rsa_key", "#HostKey /etc/ssh/ssh_host_dsa_key", "# Lifetime and size of ephemeral version 1 server key", "#KeyRegenerationInterval 1h", "#ServerKeyBits 1024", "# Logging", "# obsoletes QuietMode and FascistLogging", "#SyslogFacility AUTH", "#LogLevel INFO", "# Authentication:", "#LoginGraceTime 2m", "PermitRootLogin yes", "#StrictModes yes", "#MaxAuthTries 6", "#MaxSessions 10", "#RSAAuthentication yes", "#PubkeyAuthentication yes", "#AuthorizedKeysFile\t.ssh/authorized_keys", "# For this to work you will also need host keys in /etc/ssh/ssh_known_hosts", "#RhostsRSAAuthentication no", "# similar for protocol version 2", "#HostbasedAuthentication no", "# Change to yes if you don't trust ~/.ssh/known_hosts for", "# RhostsRSAAuthentication and HostbasedAuthentication", "#IgnoreUserKnownHosts no", "# Don't read the user's ~/.rhosts and ~/.shosts files", "#IgnoreRhosts yes", "# To disable tunneled clear text passwords, change to no here!", "#PasswordAuthentication yes", "PermitEmptyPasswords yes", "# Change to no to disable s/key passwords", "#ChallengeResponseAuthentication yes", "# Kerberos options", "#KerberosAuthentication no", "#KerberosOrLocalPasswd yes", "#KerberosTicketCleanup yes", "#KerberosGetAFSToken no", "# GSSAPI options", "#GSSAPIAuthentication no", "#GSSAPICleanupCredentials yes", "# Set this to 'yes' to enable PAM authentication, account processing,", "# and session processing. If this is enabled, PAM authentication will", "# be allowed through the ChallengeResponseAuthentication and", "# PasswordAuthentication.  Depending on your PAM configuration,", "# PAM authentication via ChallengeResponseAuthentication may bypass", "# the setting of \"PermitRootLogin without-password\".", "# If you just want the PAM account and session checks to run without", "# PAM authentication, then enable this but set PasswordAuthentication", "# and ChallengeResponseAuthentication to 'no'.", "#UsePAM no", "#AllowAgentForwarding yes", "#AllowTcpForwarding yes", "#GatewayPorts no", "#X11Forwarding no", "#X11DisplayOffset 10", "#X11UseLocalhost yes", "#PrintMotd yes", "#PrintLastLog yes", "#TCPKeepAlive yes", "#UseLogin no", "UsePrivilegeSeparation no", "#PermitUserEnvironment no", "Compression no", "ClientAliveInterval 15", "ClientAliveCountMax 4", "UseDNS no", "#PidFile /var/run/sshd.pid", "#MaxStartups 10", "#PermitTunnel no", "#ChrootDirectory none", "# no default banner path", "#Banner none", "# override default of no subsystems", "Subsystem\tsftp\t/usr/lib64/openssh/sftp-server", "# Example of overriding settings on a per-user basis", "#Match User anoncvs", "#\tX11Forwarding no", "#\tAllowTcpForwarding no", "#\tForceCommand cvs server", "#", "# Permit access from calvados and XR to host", "#", "Match Address 10.11.12.*", "PermitRootLogin yes", "#", "# Permit access from host to calvados and XR", "#", "Match Address 10.0.2.*", "PermitRootLogin yes"]</CONTENT>
					<CHECKSUM>5b4a5d15629e9a81e16d64f8a7f2e873</CHECKSUM>
					<CMD-LIST>
						<CMD>
							<REQUEST>ls -la</REQUEST>
							<RESPONSE>-rwxr-xr-x 1 root root 3466 Apr 24  2017 /etc/ssh/sshd_config</RESPONSE>
						</CMD>
					</CMD-LIST>
					<NAME>/etc/ssh/sshd_config</NAME>
				</FILE>
				<FILE>
					<CONTENT>["root:x:0:0:root:/root:/bin/sh", "daemon:x:1:1:daemon:/usr/sbin:/bin/sh", "bin:x:2:2:bin:/bin:/bin/sh", "sys:x:3:3:sys:/dev:/bin/sh", "sync:x:4:65534:sync:/bin:/bin/sync", "games:x:5:60:games:/usr/games:/bin/sh", "man:x:6:12:man:/var/cache/man:/bin/sh", "lp:x:7:7:lp:/var/spool/lpd:/bin/sh", "mail:x:8:8:mail:/var/mail:/bin/sh", "news:x:9:9:news:/var/spool/news:/bin/sh", "uucp:x:10:10:uucp:/var/spool/uucp:/bin/sh", "proxy:x:13:13:proxy:/bin:/bin/sh", "www-data:x:33:33:www-data:/var/www:/bin/sh", "backup:x:34:34:backup:/var/backups:/bin/sh", "list:x:38:38:Mailing List Manager:/var/list:/bin/sh", "irc:x:39:39:ircd:/var/run/ircd:/bin/sh", "gnats:x:41:41:Gnats Bug-Reporting System (admin):/var/lib/gnats:/bin/sh", "nobody:x:65534:65534:nobody:/nonexistent:/bin/sh", "messagebus:x:999:998::/var/lib/dbus:/bin/false", "rpc:x:998:996::/:/bin/false", "sshd:x:997:995::/var/run/sshd:/bin/false"]</CONTENT>
					<CHECKSUM>591fb16f798d29aa9dab2db5557ff4f8</CHECKSUM>
					<CMD-LIST>
						<CMD>
							<REQUEST>ls -la</REQUEST>
							<RESPONSE>-rw-r--r-- 1 root root 831 Apr 24  2017 /etc/passwd</RESPONSE>
						</CMD>
					</CMD-LIST>
					<NAME>/etc/passwd</NAME>
				</FILE>
				<FILE>
					<CHECKSUM>7ea587858977ef205c6a7419463359f7</CHECKSUM>
					<CMD-LIST>
						<CMD>
							<REQUEST>ls -la</REQUEST>
							<RESPONSE>lrwxrwxrwx 1 root root 7 Apr 24  2017 /usr/bin/python -&gt; python2</RESPONSE>
						</CMD>
					</CMD-LIST>
					<NAME>/usr/bin/python</NAME>
				</FILE>
				<FILE>
					<CONTENT>["# Defaults for dhcp initscript", "# sourced by /etc/init.d/dhcp-server", "# installed at /etc/default/dhcp-server by the maintainer scripts", "# On what interfaces should the DHCP server (dhcpd) serve DHCP requests?", "#       Separate multiple interfaces with spaces, e.g. \"eth0 eth1\".", "INTERFACES=\"\""]</CONTENT>
					<CHECKSUM>1c905007d96a8b16c58454b6da8cfd86</CHECKSUM>
					<CMD-LIST>
						<CMD>
							<REQUEST>ls -lhrt</REQUEST>
							<RESPONSE>-rw-r--r-- 1 root root 290 Apr 24  2017 /etc/default/dhcp-server</RESPONSE>
						</CMD>
					</CMD-LIST>
					<NAME>/etc/default/dhcp-server</NAME>
				</FILE>
			</FILES>
			<DIRECTORIES>
				<DIRECTORY>
					<CMD-LIST>
						<CMD>
							<REQUEST>ls -ld</REQUEST>
							<RESPONSE>drwxr-sr-x 3 root root 20480 Apr 24  2017 /usr/bin</RESPONSE>
						</CMD>
					</CMD-LIST>
					<NAME>/usr/bin</NAME>
				</DIRECTORY>
				<DIRECTORY>
					<CMD-LIST>
						<CMD>
							<REQUEST>ls -lrt</REQUEST>
							<RESPONSE>total 4
-rw-r--r-- 1 root root 97 Apr 24  2017 cmdline
-rw-r--r-- 1 root root  0 May  4 16:14 test.txt</RESPONSE>
						</CMD>
						<CMD>
							<REQUEST>touch test.txt</REQUEST>
							<RESPONSE></RESPONSE>
						</CMD>
					</CMD-LIST>
					<NAME>/root</NAME>
				</DIRECTORY>
				<DIRECTORY>
					<CMD-LIST>
						<CMD>
							<REQUEST>ls -ld</REQUEST>
							<RESPONSE>drwxr-xr-x 3 root root 4096 May  4 15:26 /misc/scratch</RESPONSE>
						</CMD>
					</CMD-LIST>
					<NAME>/misc/scratch</NAME>
				</DIRECTORY>
				<DIRECTORY>
					<CMD-LIST>
						<CMD>
							<REQUEST>ls -ld</REQUEST>
							<RESPONSE>drwxr-xr-x 7 root root 4096 May  4 16:03 /misc/app_host</RESPONSE>
						</CMD>
					</CMD-LIST>
					<NAME>/misc/app_host</NAME>
				</DIRECTORY>
				<DIRECTORY>
					<CMD-LIST>
						<CMD>
							<REQUEST>ls -ld</REQUEST>
							<RESPONSE>drwxr-sr-x 56 root root 4096 May  4 06:29 /etc</RESPONSE>
						</CMD>
					</CMD-LIST>
					<NAME>/etc</NAME>
				</DIRECTORY>
				<DIRECTORY>
					<CMD-LIST>
						<CMD>
							<REQUEST>ls -ld</REQUEST>
							<RESPONSE>drwxr-sr-x 27 root root 4096 May  4 06:29 /</RESPONSE>
						</CMD>
					</CMD-LIST>
					<NAME>/</NAME>
				</DIRECTORY>
			</DIRECTORIES>
		</INTEGRITY>
	</INTEGRITY-SET>
</COMPLIANCE-DUMP>vagrant@vagrant:~$ 

```


Excellent, how does one read this data?

The Basic structure is defined based on the XML schema `userfsfiles/compliance.xsd` in the git repo.

>**NOTE**: The XML file will only be generated by the apps if the xml content validates successfully against the `compliance.xsd` file. So if you're receiveing XML content from the collector app, then you can be rest assured that it is already validated based on the schema.


If we deconstruct parts of the XML data, we can see the basic structure starts with the <COMPLIANCE-DUMP> tag and the version of the auditor app (remember we used the `-v` option with the app earlier?) as an attribute:

```

<COMPLIANCE-DUMP xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="1.0.0" xsi:noNamespaceSchemaLocation="compliance.xsd">
....

```

The next set of higher level tags are:

1.  <GENERAL>

  ```

  <COMPLIANCE-DUMP xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="1.0.0" xsi:noNamespaceSchemaLocation="compliance.xsd">
  <GENERAL>
		<PRODUCT>XRV-P-L--CH</PRODUCT>
		<VENDOR>Cisco</VENDOR>
		<IPADDR>11.1.1.10/24</IPADDR>
		<HOST>rtr</HOST>
		<VERSION>6.1.2</VERSION>
		<DATE>20180504-16:14 UTC</DATE>
		<OS>IOS-XR</OS>
	</GENERAL>
  ```
  
  The <GENERAL> data is used to collect relevant information from the router config and oper state in order to uniquely identify the router that produced this XML content.



2. <INTEGRITY-SET>

This is the actual compliance/audit data being collected by the apps from the individual Linux shells. It can be seen from the snippets below, that the integrity set consists of three sections identified by the `domain` which can be `XR-LXC`, `ADMIN-LXC` or `HOST`.

Within each domain, there are a list of `<FILES>` each of which can be subjected to a list of commands along with content, checksum outputs. Further, there is a section called `<DIRECTORIES>` which is very similar to the `<FILES>` section and also contains a list of directories with the outputs of a list of commands on each directory.


```

	<INTEGRITY-SET>
		<INTEGRITY domain="XR-LXC">
			<FILES>
				<FILE>
					<CONTENT>["#\t$OpenBSD: sshd_config,v 1.80 2008/07/02 02:24:18 djm Exp $", "# This is the sshd server system-wide configuration file.  See", "# sshd_config(5) for more information.", "# This sshd was compiled with 
          
       ......
       
"UsePrivilegeSeparation no", "#PermitUserEnvironment no", "Compression no", "ClientAliveInterval 15", "ClientAliveCountMax 4", "UseDNS no", "#PidFile /var/run/sshd.pid", "#MaxStartups 10", "#PermitTunnel no", "#ChrootDirectory none", "# no default banner path", "#Banner none", "# override default of no subsystems", "Subsystem\tsftp\t/usr/lib64/openssh/sftp-server", "# Example of overriding settings on a per-user basis", "#Match User anoncvs", "#\tX11Forwarding no", "#\tAllowTcpForwarding no", "#\tForceCommand cvs server"]</CONTENT>
					<CHECKSUM>97884b5c2cb2b75022c4b440ddc4245a</CHECKSUM>
					<CMD-LIST>
						<CMD>
							<REQUEST>ls -la</REQUEST>
							<RESPONSE>-rwxr-xr-x 1 root root 3275 Apr 24  2017 /etc/ssh/sshd_config</RESPONSE>
						</CMD>
					</CMD-LIST>
					<NAME>/etc/ssh/sshd_config</NAME>
				</FILE>       
              
        .....
        
      </FILES>
      <DIRECTORIES>
				<DIRECTORY>
					<CMD-LIST>
						<CMD>
							<REQUEST>ls -ld</REQUEST>
							<RESPONSE>drwxr-xr-x 3 root root 20480 Apr 24  2017 /usr/bin</RESPONSE>
						</CMD>
					</CMD-LIST>
					<NAME>/usr/bin</NAME>
				</DIRECTORY>
				<DIRECTORY>

      ....
      
				</DIRECTORY>
			</DIRECTORIES>
		</INTEGRITY>
		<INTEGRITY domain="ADMIN-LXC">
			<FILES>
				<FILE>
        
        
        ....
        
        
			</DIRECTORIES>
		</INTEGRITY>
		<INTEGRITY domain="HOST">
			<FILES>
				<FILE>		  
        
        

```

>So where are the commands and the list of files and directories defined??
>This is part of the `userfiles/auditor.cfg.yml` file as well. Jump to the `COMPLIANCE_CONFIG` section and you will see a YAML specification as shown below:
><a href="https://github.com/akshshar/xr-auditor/blob/master/images/compliance_config.png?raw=true">![compliance_config](https://github.com/akshshar/xr-auditor/blob/master/images/compliance_config.png?raw=true)</a>








     
