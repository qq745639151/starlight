import subprocess

cmd = ["pip", "list"]
p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

stdout, stderr = p.communicate()
package_list = []
for line in stdout.decode("utf-8").split("\r\n")[2:]:
    package_name = line.split(" ")[0]
    if package_name and package_name not in ["pip", "wheel", "setuptools"]:
        package_list.append(package_name)

for package_name in package_list:
    cmd = ["pip", "uninstall", package_name, "-y"]
    p = subprocess.Popen(cmd)
    p.communicate()
