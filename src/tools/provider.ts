import {Command} from 'https://deno.land/x/cliffy/command/mod.ts';

export class LetheanToolsProvider {


	public static config() {
		return new Command().description('LVMGMT Replacment')
			.option('-G, --generate-providerid', 'Generate providerid files.')
			.option('-D, ---generate-sdp', 'Generate SDP by wizzard.')
			.option('-E, --edit-sdp', 'Edit existing SDP config')
			.option('-U, --upload-sdp', 'Upload SDP')
			.option('-S, --generate-server-configs', 'Generate configs for services and exit')
			.option('-C, --generate-client-config', 'Generate config for given service')
			.option('--sdp-service-crt', 'Provider Proxy crt (for SDP edit/creation only)')
			.option('--sdp-service-type', 'Service type (proxy or vpn)')
			.option('--sdp-service-name', 'Service name (for SDP service edit/creation only)')
			.option('--sdp-service-cost', 'Service cost (for SDP service edit/creation only)')
			.option('--sdp-service-disable', 'Set to true to disable service; otherwise leave false.')
			.option('--sdp-service-refunds', 'Allow refunds for Service (for SDP service edit/creation only)')
			.option('--sdp-service-dlspeed', 'Download speed for Service (for SDP service edit/creation only)')
			.option('--sdp-service-ulspeed', 'Upload speed for Service (for SDP service edit/creation only)')
			.option('--sdp-service-prepaid-mins', 'Prepaid minutes for Service (for SDP service edit/creation only)')
			.option('--sdp-service-verifications', 'Verifications needed for Service (for SDP service edit/creation only)')
			.option('--sdp-provider-name', 'Provider Name')
			.option('--sdp-provider-type', 'Provider type')
			.option('--sdp-provider-terms', 'Provider terms')
			.option('--provider-key', 'ProviderID (private ed25519 key)');

//		# Initialise config
	}
}
