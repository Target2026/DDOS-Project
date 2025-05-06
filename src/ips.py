def block_attacker(datapath, attacker_ip):
    parser = datapath.ofproto_parser
    match = parser.OFPMatch(ipv4_src=attacker_ip)
    actions = []
    inst = [parser.OFPInstructionActions(ofproto.OFPIT_CLEAR_ACTIONS, actions)]
    mod = parser.OFPFlowMod(datapath=datapath, priority=10, match=match, instructions=inst)
    datapath.send_msg(mod)
    print(f"Blocked: {attacker_ip}")

if _name_ == "_main_":
    attacker_ip = "10.0.0.5"
    block_attacker(datapath, attacker_ip)