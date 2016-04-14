#!/usr/bin/python
import logging
import configparser
import paramiko
import os
import re
import time

###define log
logging.basicConfig(level=logging.DEBUG,filename='deploy.log',filemode='w',format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s')

####define class environment
class env():
	'store environments information'
		
###read config file to load env information.
env_store=[]
plan_store=[]
get_cfg=configparser.ConfigParser()
with open('env.properties','r') as cfgfile:
	get_cfg.read_file(cfgfile)
	section_list=get_cfg.sections()
	for section in section_list:
		section=str(section)
		p=re.compile('ENV')
		if p.search(section) is not None:
		#	a=env(name= section,ip=get_cfg.get(section,'ip'),user=get_cfg.get(section,'user'),password=get_cfg.get(section,'password'),path=get_cfg.get(section,'path'),type= get_cfg.get(section,'type'))
			a = env()
			a.name = section 
			a.ip = get_cfg.get(section,'ip')
			a.user = get_cfg.get(section,'user')
			a.password = get_cfg.get(section,'password')
			a.path = get_cfg.get(section,'path')
			a.type = get_cfg.get(section,'type')
			a.db_user = ''
			a.db_password = ''
			if a.type=='DB':
				a.db_user=get_cfg.get(section,'db_user')
				a.db_password=get_cfg.get(section,'db_password')
			env_store.append(a)
		else:
			envs=get_cfg.get(section,'procedure')
			plan_store=envs.split(',')
			

print(plan_store)

def upload(package,env_name):
	for a in env_store:
		if a.name==env_name:
			p=paramiko.Transport((a.ip,22))
			p.connect(username=a.user,password=a.password)
			sftp=paramiko.SFTPClient.from_transport(p)
			local_path=os.getcwd()
			local_file=local_path+'/'+package
			remote_file=a.path+'/'+package
			print('start upload file... \n'+local_file)
			sftp.put(local_file,remote_file)
			p.close()

def deploy(package,env_name):
	for a in env_store:
		if a.name == env_name:
			upload(package,env_name)
			package_name=package.split('.')[0]
			deployment_time = time.localtime()
			newStyleDeployment_time = time.strftime("%Y_%m_%d_%H_%M_%S",deployment_time)
			package_folder = "%s_%s" %(package_name, newStyleDeployment_time)
			## ssh connect
			ssh = paramiko.SSHClient()
			ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
			ssh.connect(a.ip, username =a.user, password =a.password)
			if a.type == 'APP':
				print('start deploy application...')
				#cmd = "sleep 5 \ncd %(path)s \nunzip %(package)s -d %(package_folder)s\nmv %(package)s 123.zip\n" %{'path': a.path,'package':package, 'package_folder':package_folder}
				cmd = "cd %(path)s ;unzip %(package)s -d %(package_folder)s ;cd %(package_folder)s/scripts ;nohup sh install.sh upgrade &\n" %{'path': a.path, 'package':package, 'package_folder':package_folder}
				print(cmd)
				stdin, stdout, stderr = ssh.exec_command(cmd)
				print(stdout.read())
				#print(stdin.read())
			elif a.type == 'DB':
				print('start deploy db scripts...')
				cmd = "cd %(path)s ;unzip %(package)s -d %(package_folder)s ;cd %(package_folder)s/db ;nohup sh upgrade_db.sh %(db_user)s %(db_password)s &\n" %{'path': a.path, 'package':package, 'package_folder': package_folder, 'db_user': a.db_user, 'db_password': a.db_password}
				stdin, stdout, stderr = ssh.exec_command(cmd)
				print(stdout.read())
			else:
				print("The type of environment is not supported, only 'APP' and 'DB' are supported. Please modify env.properties")
				ssh.close()
				exit()
			ssh.close()	


##package=input("Please input package's name:\n")
def get_package():
	package=[]
	file_list= os.listdir()
	for f in file_list:
		name,ext= os.path.splitext(f)
		if ext=='.zip':
			package.append(f)
	if len(package) > 1:
		print("Found more than one package at current path, multi-package deployment is not supported.")
		quit()
	else:
		return package[0]

package= get_package() 

print('start deploy this package: '+package)
package_full=os.getcwd()+'/'+package
if os.path.exists(package_full):
	for i in plan_store:
		for j in env_store:
			if j.name==i:
				deploy(package,j.name)
else:
	print("Can't found package at path "+os.getcwd())
		
