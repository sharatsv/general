import os
import time
import re

# Defines
monkey_apps = {'CART': ('cart-total-monkey.yaml','cart-total.yaml'),
               'CATALOG': ('catalog-total-monkey.yaml', 'catalog-total.yaml'),
               'USERS': ('users-total-monkey.yaml', 'users-total.yaml'),
               'PAYMENT': ('payment-total-monkey.yaml', 'payment-total.yaml'),
               'ORDER': ('order-total-monkey.yaml', 'order-total.yaml')
              }


def monitor_monkey(_time, monkey_pod):
    start_time = int(time.time())
    time.sleep(5)
    end_time = int(time.time())
    # print(end_time - start_time)
    while end_time - start_time <= _time:
        out = os.popen('kubectl logs %s\
                       -n acme --tail 20' %monkey_pod).read()
        print('KUBE-MONKEY logs: \n %s' % out)
        time.sleep(30)
        end_time = int(time.time())
    return


# Driver-code
if __name__ == '__main__':
    raw_pods = os.popen('kubectl get pods -n acme -o json | jq .items[].metadata.name').read()
    all_pods = raw_pods.replace('"', '').split('\n')
    kube_monkey_pod = [pod for pod in all_pods if re.search('kube-monkey', pod)]
    if len(kube_monkey_pod) == 0:
        print('Kube monkey not running! Exiting..')
        raise SystemExit, 0 
    
    while 1:
        for app in monkey_apps:
	    create_chaos = monkey_apps[app][0]
	    out = os.popen('kubectl apply -f %s -n acme' % create_chaos).read()
	    print('%s app MONKEY-victim start: \n %s' % (app, out))

        monitor_monkey(240, kube_monkey_pod[0])
 
        for app in monkey_apps:
	    resolve_chaos = monkey_apps[app][1]
	    out = os.popen('kubectl apply -f %s -n acme' % resolve_chaos).read()
	    print('%s app patched: \n %s' % (app, out))
    
        print('Sleeping 4min before next iteration \n\n')
        time.sleep(240)
