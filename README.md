## 1. create test logs

```bash
# Default 1MB, hostname server-prod-uk-01
python3 generate_test_logs.py

# Specific size
python3 generate_test_logs.py -s 500KB
python3 generate_test_logs.py -s 10MB
python3 generate_test_logs.py -s 2GB

# Custom hostname and output dir
python3 generate_test_logs.py -s 5MB --hostname web-prod-lon-03 --out /tmp

# Reproducible output (same seed = same file every time)
python3 generate_test_logs.py -s 1MB --seed 99
```

```bash
mickm@ubuntu24-2:~/obfuscation$ python3 generate_test_logs.py -s 500KB
Generating 500.0KB of log data (seed=42)...
Writing test_logs_server-prod-uk-01.zip...
Done.
  Log size (uncompressed) : 512,000 bytes (500.0KB)
  Zip size (compressed)   : 112,602 bytes
  Compression ratio       : 4.5x
  Output                  : test_logs_server-prod-uk-01.zip
mickm@ubuntu24-2:~/obfuscation$ 
```

## 2. obfuscate the logs

```bash
python3 obfuscate_logs.py test_logs_server-prod-uk-01.zip
```

```bash
mickm@ubuntu24-2:~/obfuscation$ python3 obfuscate_logs.py test_logs_server-prod-uk-01.zip
[1/4] Scanning for IPs in test_logs_server-prod-uk-01.zip...
      Found 6300 unique IPs
[2/4] Writing mapping files...
[3/4] Obfuscating and writing logs_ca2052293615066b_obfuscated.zip...
[4/4] Done.
      Obfuscated zip : logs_ca2052293615066b_obfuscated.zip
      Encode map     : obfuscation_encode.txt
      Decode map     : obfuscation_decode.txt
mickm@ubuntu24-2:~/obfuscation$ 
```

## 3. verify the obfuscation

```
unzip logs_ca2052293615066b_obfuscated.zip
head log_63762c42cd07.log
head obfuscation_encode.txt
head obfuscation_decode.txt
```

```bash
mickm@ubuntu24-2:~/obfuscation$ unzip logs_ca2052293615066b_obfuscated.zip
Archive:  logs_ca2052293615066b_obfuscated.zip
  inflating: log_63762c42cd07.log
mickm@ubuntu24-2:~/obfuscation$ 
mickm@ubuntu24-2:~/obfuscation$ ls -ltr
total 1312
-rw-r--r-- 1 mickm mickm   3662 Jun 10 10:19 v1_obfuscate_logs.py
-rw-r--r-- 1 mickm mickm   9554 Jun 10 10:24 generate_test_logs.py
-rw-r--r-- 1 mickm mickm   7202 Jun 10 10:51 obfuscate_logs.py
-rw-r--r-- 1 mickm mickm 112602 Jun 10 10:52 test_logs_server-prod-uk-01.zip
-rw------- 1 mickm mickm 569256 Jun 10 10:53 log_63762c42cd07.log
-rw-r--r-- 1 mickm mickm 253574 Jun 10 10:53 obfuscation_encode.txt
-rw-r--r-- 1 mickm mickm 253574 Jun 10 10:53 obfuscation_decode.txt
-rw-r--r-- 1 mickm mickm 124814 Jun 10 10:53 logs_ca2052293615066b_obfuscated.zip
mickm@ubuntu24-2:~/obfuscation$
mickm@ubuntu24-2:~/obfuscation$ head log_63762c42cd07.log
OBFUSC_110.188.153.124 - nagios [Jun 01 10:00:48] "GET /api/v1/health HTTP/1.1" 200 512 "-" "curl/7.81.0"
Jun 01 15:21:42 web-prod-uk-01 sshd[7140]: [DEBUG] Disconnected from OBFUSC_203.146.162.105 port 30463
Jun 01 05:48:46 lb-prod-uk-01 postfix[19210]: [DEBUG] Connection from OBFUSC_040.071.161.138 port 23565 on OBFUSC_135.090.222.062 port 22
OBFUSC_198.033.228.039 - - [Jun 01 04:32:41] "GET / HTTP/1.1" 301 185 "-" "python-requests/2.28.0"
2026-06-01T13:10:00.591Z FIREWALL: ACCEPTED IN=eth0 OUT= SRC=OBFUSC_011.182.194.223 DST=OBFUSC_215.076.145.189 PROTO=UDP SPT=14754 DPT=53
Jun 01 23:35:39 web-prod-uk-02 sudo[42613]: [WARN] Connection from OBFUSC_101.056.162.250 port 61670 on OBFUSC_206.039.196.055 port 22
OBFUSC_006.248.113.003 - nagios [Jun 01 08:20:21] "GET /api/v1/health HTTP/1.1" 200 512 "-" "curl/7.81.0"
2026-06-01T11:27:25.217Z FIREWALL: BLACKLIST match SRC=OBFUSC_030.154.244.105 DST=OBFUSC_222.106.111.008 DPT=5432
Jun 01 01:42:55 web-prod-uk-02 kernel[42120]: [NOTICE] Connection from OBFUSC_183.132.088.195 port 31698 on OBFUSC_010.094.119.232 port 22
2026-06-01T00:25:04.696Z FIREWALL: DROPPED IN=eth0 OUT= SRC=OBFUSC_020.176.098.187 DST=OBFUSC_076.182.206.154 PROTO=TCP SPT=50959 DPT=80 FLAGS=SYN
mickm@ubuntu24-2:~/obfuscation$
mickm@ubuntu24-2:~/obfuscation$ head obfuscation_encode.txt
# === HOSTNAMES ===
server-prod-uk-01 -> OBFUSC-HOST-F69B7CE7
# === IP ADDRESSES ===
1.110.23.76 -> OBFUSC_167.214.055.013
1.118.160.250 -> OBFUSC_048.104.252.095
1.13.240.175 -> OBFUSC_141.094.098.040
1.182.232.252 -> OBFUSC_029.127.166.194
1.184.198.34 -> OBFUSC_014.183.226.148
1.201.60.254 -> OBFUSC_002.232.023.235
1.211.237.50 -> OBFUSC_029.251.019.207
mickm@ubuntu24-2:~/obfuscation$ 
mickm@ubuntu24-2:~/obfuscation$ head obfuscation_decode.txt
# === HOSTNAMES ===
OBFUSC-HOST-F69B7CE7 -> server-prod-uk-01
# === IP ADDRESSES ===
OBFUSC_167.214.055.013 -> 1.110.23.76
OBFUSC_048.104.252.095 -> 1.118.160.250
OBFUSC_141.094.098.040 -> 1.13.240.175
OBFUSC_029.127.166.194 -> 1.182.232.252
OBFUSC_014.183.226.148 -> 1.184.198.34
OBFUSC_002.232.023.235 -> 1.201.60.254
OBFUSC_029.251.019.207 -> 1.211.237.50
mickm@ubuntu24-2:~/obfuscation$
```
## 4 after the obfuscation we can still see hostnames e.g. web-prod-uk-01 - so the script `obfuscate_logs.py` - might need further modifications after we get a real set of logs to test against


```
mickm@ubuntu24-2:~/obfuscation$ head log_63762c42cd07.log
OBFUSC_110.188.153.124 - nagios [Jun 01 10:00:48] "GET /api/v1/health HTTP/1.1" 200 512 "-" "curl/7.81.0"
Jun 01 15:21:42 web-prod-uk-01 sshd[7140]: [DEBUG] Disconnected from OBFUSC_203.146.162.105 port 30463
Jun 01 05:48:46 lb-prod-uk-01 postfix[19210]: [DEBUG] Connection from OBFUSC_040.071.161.138 port 23565 on OBFUSC_135.090.222.062 port 22
OBFUSC_198.033.228.039 - - [Jun 01 04:32:41] "GET / HTTP/1.1" 301 185 "-" "python-requests/2.28.0"
2026-06-01T13:10:00.591Z FIREWALL: ACCEPTED IN=eth0 OUT= SRC=OBFUSC_011.182.194.223 DST=OBFUSC_215.076.145.189 PROTO=UDP SPT=14754 DPT=53
Jun 01 23:35:39 web-prod-uk-02 sudo[42613]: [WARN] Connection from OBFUSC_101.056.162.250 port 61670 on OBFUSC_206.039.196.055 port 22
OBFUSC_006.248.113.003 - nagios [Jun 01 08:20:21] "GET /api/v1/health HTTP/1.1" 200 512 "-" "curl/7.81.0"
2026-06-01T11:27:25.217Z FIREWALL: BLACKLIST match SRC=OBFUSC_030.154.244.105 DST=OBFUSC_222.106.111.008 DPT=5432
Jun 01 01:42:55 web-prod-uk-02 kernel[42120]: [NOTICE] Connection from OBFUSC_183.132.088.195 port 31698 on OBFUSC_010.094.119.232 port 22
2026-06-01T00:25:04.696Z FIREWALL: DROPPED IN=eth0 OUT= SRC=OBFUSC_020.176.098.187 DST=OBFUSC_076.182.206.154 PROTO=TCP SPT=50959 DPT=80 FLAGS=SYN
mickm@ubuntu24-2:~/obfuscation$
```
