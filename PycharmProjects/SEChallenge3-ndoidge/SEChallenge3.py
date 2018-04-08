#!/usr/bin/env python

from global_definitions import switch_info
from switch_class import switch, credentials





def main():
    #create an instance of the switch class
    nxos = switch(switch_info)

    #login to the switch and only proceed if the login returns successful
    if nxos.aaaLogin():
        print 'Successfully logged into the switch, beginning feature checks...'
        enabled = 1 #variable used to track if the interface-vlan feature is enabled

        #check if the interface-vlan feature is enabled
        if nxos.is_feature_enabled('fmInterfaceVlan') == 0:
            enabled = 0
            #if not enabled try three times to enable it
            for i in range(0, 3):
                #if the feature is enabled, then
                if nxos.enable_feature('interface-vlan'):
                    enabled = 1
                    break

        if enabled == 0:
            print 'Tried to enable the interface-vlan feature, but failed, exiting...'
            return 0

        #if we have got this far then the feature is (or had previously been) enabled so lets make some vlans!
        #I had thought about building one big dictionary with all the VLANs I want to add, allowing a single REST call
        #for all VLANS. Whilst this way is less efficient I have opted to do one at a time so you could call the
        #function many times over making the structure of the function call easier

        for i in range (5, 255, 5):
            if nxos.create_vlan(i, 'auto-generated vlan-' + str(i)):
                print 'Created VLAN ' + str(i)
            else:
                print 'Failed to create VLAN ' + str(i)


if __name__ == "__main__":
    main()
    details = credentials('127.0.0.1', 'vagrant', 'vagrant')

    print details.password
    print details.url