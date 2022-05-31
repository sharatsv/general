import yaml
import os
import time
import json
import re

BASE_PATH = '/Users/ssharat/Documents/'
INPUT_YAML = BASE_PATH + 'acme/acme_fitness_demo/deploy_acme_aws.yaml'
KUBE_CONF = '/Users/ssharat/Documents/acme/acme_aws_ssharat/kubeconfig-ssharat-aws-cluster.yml'
# Customize kubectl to comprise kubeconfig path
KUBECTL = 'kubectl --kubeconfig %s' % KUBE_CONF

class DeployApplication(object):
    def __init__(self, _yaml, _app):
        try:
            with open(_yaml, "r") as stream:
                self._app = _app
                self.deploy_info = yaml.load(stream, Loader=yaml.FullLoader)
                self.deployments = []
                # Extract features
                self.ns = self.deploy_info[_app]['namespace']
                if self._app == 'acme_application':
                    node_label_map = self.deploy_info[_app]['nodeselector']
                    if node_label_map:
                        for node, label in node_label_map.items():
                            _ = os.system('%s label nodes %s %s' % (KUBECTL, node, label))
                    self.secrets = self.deploy_info[_app]['secret']
                    self.deployments = self.deploy_info[_app]['deploy']
                    self.configmaps = self.deploy_info[_app]['configmap']
                elif self._app == 'wavefront_application':
                    self.token = self.deploy_info[_app]['api_token']
                    self.url = self.deploy_info[_app]['wavefront_url']
                    self.cluster = self.deploy_info[_app]['cluster_name']
        except OSError:
            print('File not found - check path!')
            return
        except IndexError:
            print('Application %s not found in YAML' % _app)
            return

    def check_deployment(self):
        cmd = '%s get pods -n %s -o json | jq' % (KUBECTL, self.ns)
        get_pods_raw = os.popen(cmd).read().strip().replace('\n', '')
        get_pods_json = json.loads(get_pods_raw)
        for _item in get_pods_json['items']:
            # print(_item['status']['phase'], _item['metadata']['name'])
            if _item['status']['phase'] != 'Running':
                print("POD %s in state %s" % (_item['metadata']['name'], _item['status']['phase']))
                print("Sleep 10sec and retry!")
                time.sleep(10)
                return self.check_deployment()
        print('All PODs in running state')

    def create_ns(self):
        _ = os.system("%s create ns %s" % (KUBECTL, self.ns))

    def create_secret(self):
        for secret in self.secrets:
            _ = os.system('%s create secret %s -n %s' % (KUBECTL, secret, self.ns))

    def deploy(self):
        for deploy in self.deployments:
            print('Deploying %s in ns %s' % (deploy, self.ns))
            _ = os.system('%s apply -f %s -n %s' % (KUBECTL, deploy, self.ns))
            self.check_deployment()
        # Start essential services
        if self._app == 'acme_application':
            print('Starting Front-End application:')
            #out = os.popen('minikube service --url frontend -n %s' % self.ns).read()
            #print(out)
        elif self._app == 'wavefront_application':
            print('Deploying wavefront proxy and collector using helm-charts')
            out = os.popen('helm install wavefront wavefront/wavefront '
                           '--set wavefront.url=%s '
                           '--set wavefront.token=%s ' 
                           '--set clusterName=%s '
                           '--namespace=%s' % (self.url, self.token, self.cluster, self.ns)).read()
            print(out)

    def create_configmap(self):
        for configmap in self.configmaps:
            _ = os.system('%s create -f %s -n %s' % (KUBECTL, configmap,  self.ns))

    def update_config(self):
        '''
        Function to update config due to change of dynamic config params
        :return:
        '''
        # Fetch the ip-address of Jaeger POD in acme namespace and update the
        # deployment yamls
        cmd = '%s get pods -n %s -o json | jq' % (KUBECTL, self.ns)
        get_pods_raw = os.popen(cmd).read().strip().replace('\n', '')
        get_pods_json = json.loads(get_pods_raw)
        for _item in get_pods_json['items']:
            if 'jaeger' in _item['metadata']['name']:
                pod_ip = _item['status']['podIP']
                break
        # Replace jaeger-agent host in deployment files
        for deploy in self.deployments:
            new_file_content = ""
            replace_str = False
            print(deploy)
            read_file = open(deploy, 'r')
            print('Replacing pod-ip %s in file %s' % (pod_ip, deploy))
            for line in read_file:
                if replace_str:
                    line = re.sub("value.*", "value: \'%s\'" % pod_ip, line)
                    replace_str = False
                if 'JAEGER_AGENT_HOST' in line:
                    replace_str = True
                new_file_content += line
            read_file.close()
            write_file = open(deploy, "w")
            write_file.write(new_file_content)
            write_file.close()


# Driver-code
if __name__ == '__main__':
    # Workflow-1: Instantiate class to deploy acme microservices
    acme = DeployApplication(INPUT_YAML, 'acme_application')
    acme.create_ns()
    # acme.update_config()
    acme.create_secret()
    acme.create_configmap()
    acme.deploy()
    # Workflow-2: Instantiate class to deploy wf
    # wf = DeployApplication(INPUT_YAML, 'wavefront_application')
    # wf.create_ns()
    # wf.deploy()
