import {Command} from 'https://deno.land/x/cliffy/command/mod.ts';
import {encode as he} from "https://deno.land/std/encoding/hex.ts";
const td=(d:Uint8Array)=>new TextDecoder().decode(d);

export class LetheanAccount {

    public static async create(args: any) {
		console.log('yo')
		console.log(args)


		const keyPair = await crypto.subtle.generateKey({
				name: "RSA-OAEP",
				modulusLength: 2048,
				publicExponent: new Uint8Array([1, 0, 1]),
				hash: "SHA-512",
			},
			true,
			["encrypt", "decrypt"],
		);

		console.log(keyPair.privateKey, keyPair.publicKey)
		const exportedPrivateKeyBuffer = await crypto.subtle.exportKey(
			"pkcs8",
			keyPair.privateKey,
		);
		const exportedPublicKeyBuffer = await crypto.subtle.exportKey(
			"spki",
			keyPair.publicKey,
		);
		const privateKey=td(he(new Uint8Array(exportedPrivateKeyBuffer)));
		const pubKey=td(he(new Uint8Array(exportedPublicKeyBuffer)));
		//return {"public": pubKey, "private" :privateKey}
	}


	public static config() {
		return new Command().description('Lethean Account Management')
			.command('create', 'Create an Account on the filesystem')
			.option('-n, --name <string>', 'Username to use')
			.option('-p, --password <string>', 'Password')
			.action((args) => LetheanAccount.create(args))
			;

//		# Initialise config
	}

}
