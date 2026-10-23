# Aster Setup Guide

### Note: This guide was written during the Fall 2026 semester. Some information may be outdated and should be double-checked if any issues are encountered.

## Step 1: VPN Setup
The GlobalProtect VPN is required access the aster cluster remotely. You can find the download located at https://software.pitt.edu.  


In the GlobalProtect, enter `portal-palo.pitt.edu` in the portal address field. 

Use your Pitt credentials when prompted for your username and password.


### Step 2: Connecting to an Aster Server

Establish an SSH connection using your Pitt username and the desired Aster server:

```bash
ssh <Pitt-username>@asterx.cs.pitt.edu
```
where x is an integer in the range 1-20.


Example:
```bash
ssh abc12@aster_LAN_1.cs.pitt.edu
```

Use your Pitt password to login to the cluster. I initially had issues  with this and had to contact IT.

### Step 3: Dependencies

The Aster cluster runs AlmaLinux 9, which uses `dnf` instead of Ubuntu's `apt-get` package manager.

The following dependencies are required to compile Prime and Spines:

```bash
sudo dnf install -y \
    gcc \
    gcc-c++ \
    make \
    openssl-devel \
    flex \
    bison \
    byacc \
    git \
    groff \
    python3 \
    iproute \
    iputils
```

**Note:** Most dependencies are already installed on the Aster servers. Installing additional packages requires administrator privileges.

### Step 4: Clone the Git repo
```bash
git clone https://github.com/sam444555/cs2910.git
```





## Aster Server Network Configuration [As of 10/8/2026]

| Server | Pitt Network | Local Network 1 | Local Network 2 |
|--------|--------------|-----------------|-----------------|
| aster1 | 10.27.1.10 | 192.168.53.10 | 192.168.54.10 |
| aster_LAN_2 | 10.27.1.11 | 192.168.53.11 | 192.168.54.11 |
| aster3 | 10.27.1.12 | 192.168.53.12 | 192.168.54.12 |
| aster4 | 10.27.1.13 | 192.168.53.13 | 192.168.54.13 |
| aster5 | 10.27.1.14 | 192.168.53.14 | 192.168.54.14 |
| aster6 | 10.27.1.15 | 192.168.53.15 | 192.168.54.15 |
| aster7 | 10.27.1.16 | 192.168.53.16 | 192.168.54.16 |
| aster8 | 10.27.1.17 | 192.168.53.17 | 192.168.54.17 |
| aster9 | 10.27.1.18 | 192.168.53.18 | 192.168.54.18 |
| aster10 | 10.27.1.19 | 192.168.53.19 | 192.168.54.19 |
| aster11 | 10.27.1.20 | 192.168.53.20 | 192.168.54.20 |
| aster12 | 10.27.1.21 | 192.168.53.21 | 192.168.54.21 |
| aster13 | 10.27.1.22 | 192.168.53.22 | 192.168.54.22 |
| aster14 | 10.27.1.23 | 192.168.53.23 | 192.168.54.23 |
| aster15 | 10.27.1.24 | 192.168.53.24 | 192.168.54.24 |
| aster16 | 10.27.1.25 | 192.168.53.25 | 192.168.54.25 |
| aster17 | 10.27.1.26 | 192.168.53.26 | 192.168.54.26 |
| aster18 | 10.27.1.27 | 192.168.53.27 | 192.168.54.27 |
| aster19 | 10.27.1.28 | 192.168.53.28 | 192.168.54.28 |
| aster_LAN_20 | 10.27.1.29 | 192.168.53.29 | 192.168.54.29 |
