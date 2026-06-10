


```
mickm@ubuntu24-2:~/obfuscation$ ls -ltr
total 128
-rw-r--r-- 1 mickm mickm   3662 Jun 10 10:19 obfuscate_logs.py
-rw-r--r-- 1 mickm mickm   9554 Jun 10 10:24 generate_test_logs.py
-rw-r--r-- 1 mickm mickm 112602 Jun 10 10:25 test_logs_server-prod-uk-01.zip
mickm@ubuntu24-2:~/obfuscation$ python3 obfuscate_logs.py test_logs_server-prod-uk-01.zip
[1/4] Scanning for IPs in test_logs_server-prod-uk-01.zip...
      Found 6300 unique IPs
[2/4] Writing mapping files...
[3/4] Obfuscating and writing logs_ca2052293615066b_obfuscated.zip...
[4/4] Done.
      Obfuscated zip : logs_ca2052293615066b_obfuscated.zip
      Encode map     : obfuscation_encode.txt
      Decode map     : obfuscation_decode.txt
mickm@ubuntu24-2:~/obfuscation$ ls -ltr
total 748
-rw-r--r-- 1 mickm mickm   3662 Jun 10 10:19 obfuscate_logs.py
-rw-r--r-- 1 mickm mickm   9554 Jun 10 10:24 generate_test_logs.py
-rw-r--r-- 1 mickm mickm 112602 Jun 10 10:25 test_logs_server-prod-uk-01.zip
-rw-r--r-- 1 mickm mickm 253489 Jun 10 10:25 obfuscation_encode.txt
-rw-r--r-- 1 mickm mickm 253489 Jun 10 10:25 obfuscation_decode.txt
-rw-r--r-- 1 mickm mickm 124836 Jun 10 10:25 logs_ca2052293615066b_obfuscated.zip
mickm@ubuntu24-2:~/obfuscation$ unzip  logs_ca2052293615066b_obfuscated.zip
Archive:  logs_ca2052293615066b_obfuscated.zip
  inflating: test_logs_server-prod-uk-01.log
mickm@ubuntu24-2:~/obfuscation$ head  test_logs_server-prod-uk-01.log
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
mickm@ubuntu24-2:~/obfuscation$ sum obfuscate_logs.py
61412     4 obfuscate_logs.py
mickm@ubuntu24-2:~/obfuscation$ sum  generate_test_logs.py
60427    10 generate_test_logs.py
mickm@ubuntu24-2:~/obfuscation$ wc -l obfuscate_logs.py
104 obfuscate_logs.py
mickm@ubuntu24-2:~/obfuscation$ wc -l generate_test_logs.py
263 generate_test_logs.py
mickm@ubuntu24-2:~/obfuscation$ zip obfuscate_logs_python.zip obfuscate_logs.py generate_test_logs.py
  adding: obfuscate_logs.py (deflated 59%)
  adding: generate_test_logs.py (deflated 65%)
mickm@ubuntu24-2:~/obfuscation$ ls -ltr
total 1312
-rw-r--r-- 1 mickm mickm   3662 Jun 10 10:19 obfuscate_logs.py
-rw-r--r-- 1 mickm mickm   9554 Jun 10 10:24 generate_test_logs.py
-rw------- 1 mickm mickm 569256 Jun 10 10:25 test_logs_server-prod-uk-01.log
-rw-r--r-- 1 mickm mickm 112602 Jun 10 10:25 test_logs_server-prod-uk-01.zip
-rw-r--r-- 1 mickm mickm 253489 Jun 10 10:25 obfuscation_encode.txt
-rw-r--r-- 1 mickm mickm 253489 Jun 10 10:25 obfuscation_decode.txt
-rw-r--r-- 1 mickm mickm 124836 Jun 10 10:25 logs_ca2052293615066b_obfuscated.zip
-rw-r--r-- 1 mickm mickm   5164 Jun 10 10:31 obfuscate_logs_python.zip
mickm@ubuntu24-2:~/obfuscation$ sum obfuscate_logs_python.zip
23412     6 obfuscate_logs_python.zip
mickm@ubuntu24-2:~/obfuscation$
```
