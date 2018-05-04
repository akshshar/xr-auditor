# Auditor

## Introduction

This application enables **periodic auditing** of the linux shells in the IOS-XR container-based architecture by running **individual python applications in each individual environment in IOS-XR   
(across Active-Standby HA systems)**, i.e.:  

>*   XR-LXC     
>*   ADMIN-LXC   
>*   HOST    
  

**Functionally**, the individual python applications:  

>*  **Collect local data based on a YAML based user-config** provided during the build process 
>*  **Store accummulated data in the form of XML that is strictly validated against a user-defined XML schema**.
>*  **Send the accummulated XML data periodically to an external server over SSH** where it may be easily processed and visualized using any tools that can consume the XML schema and the data.

Further, the **application supports**:  

>1.  **Installation**: on a High-Availability (Active/Standby RP) system through a single command.  
>2.  **A clean uninstallation**  across the entire system through a single command.  
>3.  **Troubleshooting**:   **Dump filesystem view** - The ability to view the entire system's affected (user-defined in YAML file) system across active/standby RPs using a single command.  
>4.  **Troubleshooting**:   **Gather debug Data** - The ability to collect generated logs from all the environments (Active/Standby XR LXC, Admin LXC, HOST) and create a single tar ball using a single command.  
    
    
No SMUs needed, leverages the native app-hosting architecture in IOS-XR and the internal SSH-based access between different parts of the IOS-XR architecture - namely, XR-LXC, Admin-LXC and HOST of the active and/or Standby RPs to easily manage movement of data, logs and apps across the system.




## User Story

As in the development of any application, it is best to first construct a user story out of the requirements listed by an end-user, in this case a Service Provider customer that we worked with:

The user-story that results is shown below:
| User Requirements                                                          | Application Capabilities                                                                                                                                                                                                                                                                                 |
|----------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Collect periodic data from all linux environments in the system            | Run Cron Jobs to collect data in XR-LXC, Admin-LXC and Host linux environments in IOS-XR                                                                                                                                                                                                                 |
| One Step installation                                                      | /misc/scratch/auditor  -i   installs the required python applications on the entire system.                                                                                                                                                                                                              |
| One Step uninstallation                                                    | /misc/scratch/auditor -u -c    uninstalls and cleans up apps and generated files  from the entire system.                                                                                                                                                                                                |
| Collect data in each shell in a structured format  (preference: XML)       | An XML-Schema is used to validate the generated data and resultant XML can be converted into json, yaml and other formats.                                                                                                                                                                               |
| Collect a single file/stream of data for the entire system                 | A collector app periodically combines the XML data generated from XR-LXC, Admin-LXC and Host, validates against the XML schema and generates a single XML data file                                                                                                                                      |
| Easy to troubleshoot:  View State                                          | Supports the capability to "list" the directories across the entire filesystem to quickly check the files being created by the apps on the router                                                                                                                                                        |
| Easy to troubleshoot:  Collect logs                                        | To support troubleshooting any issues with individual apps,  the logs generated by the individual apps in each domain (XR LXC, Admin LXC, Host) can be collected and packed into a single tar ball                                                                                                       |
| Support across platforms                                                   | The capabilities that the application uses is platform independent for all container-based IOS-XR platforms.                                                                                                                                                                                             |
| Support for Active/Standby RPs (not an explicit request from the customer) | (Good problem to solve) The application supports all the capabilities described above for both the active and Standby RPs. A Single step installation, uninstallation, collection of data across all domains on active and standby RPs, collation of data and export of data from the current Active RP) |
| Support for Switchover scenario                                            | Cisco IOS-XR platforms support application hosting consistently across HA (High-availability : Active/Standby) systems                                                                                                                                                                                   |
|                                                                            |                                                                                                                                                                                                                                                                                                          |
|                                                                            |                                                                                                                                                                                                                                                                                                          |
|                                                                            |                                                                                                                                                                                                                                                                                                          |
|                                                                            |                                                                                                                                                                                                                                                                                                          |








    
