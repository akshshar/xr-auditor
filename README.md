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




## User Story (Click to Expand)

<a href="https://raw.githubusercontent.com/akshshar/xr-auditor/master/user_story_auditor.png">![user-story](https://raw.githubusercontent.com/akshshar/xr-auditor/master/user_story_auditor.png)</a>



## IOS-XR architecture

For a quick refresher on the IOS-XR container based architecture, see the figure below:  

<a href="https://github.com/akshshar/xr-auditor/blob/master/IOS-XR-architecture.png?raw=true">![iosxr-architecture](https://github.com/akshshar/xr-auditor/blob/master/IOS-XR-architecture.png?raw=true)</a>

&nsbp;  

As shown above, access to the linux shells (in blue inside the containers) and the underlying shells is protected through XR AAA authentication and authorization.
While IOS-XR supports the 3 A's of AAA (Authentication, Authorization and Accounting),  Linux supports only 2 of them: Authentication and authorization.  
Usually accounting is handled through separate tools such as auditd, snoopy etc. We showcase the usage of snoopy with IOS-XR here:  <https://github.com/akshshar/snoopy-xr>    

Further, Linux doesn't really have a telemetry system by default - there are variety of solutions available that can provide structured data for various individual applications and files on the system, but none of them support a clean one step installation, collection and troubleshooting capabilities across container based architecture as shown above.  

This is where [xr-auditor](https://github.com/akshshar/xr-auditor) shines. It allows a user to specify their collection requirements through YAML files, build the application into single binary and deploy the auditors in each domain(container) of the system in a couple of steps.
  
  
xr-auditor is installed using a single binary generated out of the code in this git repo using pyinstaller. More details below. The installation involves running the binary on the XR-LXC shell of the Active RP: 

<a href="https://github.com/akshshar/xr-auditor/blob/master/iosxr-auditor-install.png?raw=true">![xr-auditor-install](https://github.com/akshshar/xr-auditor/blob/master/iosxr-auditor-install.png?raw=true)</a>

&nbsp;  
&nbsp;  

Once the install is triggered, individual cron jobs and apps are set up in the different domains as shown below to start sending collected data periodically to a remote server (identified in the SERVER_CONFIG in `userfiles/auditor.cfg.yml`) securely over SSH:
  
<a href="https://github.com/akshshar/xr-auditor/blob/master/iosxr-auditor-operation.png?raw=true">![xr-auditor-install](https://github.com/akshshar/xr-auditor/blob/master/iosxr-auditor-operation.png?raw=true)</a> 

&nsbp;
&nbsp;



  




## Setting up the application environment





    
