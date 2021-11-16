import {Command} from 'https://deno.land/x/cliffy/command/mod.ts';
import os from 'https://deno.land/x/dos@v0.11.0/mod.ts';
import {download, Destination} from 'https://deno.land/x/download/mod.ts';
import {unZipFromFile} from 'https://deno.land/x/zip@v1.1.0/mod.ts';
import * as path from 'https://deno.land/std/path/mod.ts';
import {copy} from 'https://deno.land/std@0.95.0/fs/mod.ts';
import {StringResponse} from './string-response.ts';

import {UpgradeCommand, GithubProvider} from 'https://deno.land/x/cliffy/command/upgrade/mod.ts';

export class LetheanUpdater {

	public static downloads = {
		cli: {
			windows: 'https://github.com/letheanVPN/lethean/releases/download/v3.1.0/lethean-cli-win-64bit-v3.1.zip',
			linux: 'https://github.com/letheanVPN/lethean/releases/download/v3.1.0/lethean-cli-linux-64bit-v3.1.zip',
			macos: 'https://github.com/letheanVPN/lethean/releases/download/v3.1.0/lethean-cli-mac-64bit-v3.1.zip'
		}
	};

	static async download(args: any) {

		let url, platform = os.platform(), homeDir = os.homeDir();

		console.log(`Downloading files for ${platform}`);

		switch (platform) {
			case 'darwin':
				url = LetheanUpdater.downloads.cli.macos;
				break;
			case 'linux':
				url = LetheanUpdater.downloads.cli.linux;
				break;
			case 'windows':
				url = LetheanUpdater.downloads.cli.windows;
				break;
		}
		let filename = url.split('/').pop();
		try {

			const destination: Destination = {
				file: filename,
				dir: path.join(homeDir ? homeDir : '', 'Lethean')
			};
			const fileObj = await download(url, destination);
			console.log(`Downloaded file to ${fileObj.fullPath}`);
			console.log('removing old binaries');
			try {
				await Deno.remove(path.join(homeDir ? homeDir : '', 'Lethean', 'cli'), {recursive: true});
			} catch (e) {
			}

			console.log(`Unpacking Downloaded zip to: ${path.join(homeDir ? homeDir : '', 'Lethean', 'cli')}`);

			await unZipFromFile(fileObj.fullPath, path.join(homeDir ? homeDir : '', 'Lethean', 'cli'), {includeFileName: false});
			console.log('Copying files');
			await copy(path.join(homeDir ? homeDir : '', 'Lethean', 'cli', `${filename?.replace('.zip', '')}`), path.join(homeDir ? homeDir : '', 'Lethean', 'cli'), {overwrite: true});
			console.log('Cleaning up');
			await Deno.remove(path.join(homeDir ? homeDir : '', 'Lethean', 'cli', `${filename?.replace('.zip', '')}`), {recursive: true});
			await Deno.remove(fileObj.fullPath);
			console.log('FIN');
		} catch (err) {
			console.log('ERROR, the following log might have helpful information.');
			console.log(err);
		}
		return 'done';
	}

	public static config() {
		return new Command().description('Lethean Updater Service')
			.command('lthn',
				new UpgradeCommand({
					provider: [
						new GithubProvider({repository: 'letheanVPN/dvpn', branches: true})
					]
				}))
			.description('Update lthn')
			.command('cli', 'Downloads the latest CLI binaries')
			.action(async (args) => {

				await LetheanUpdater.download(args).then((dat) => {
					if (Deno.env.get('REST')) {
						throw new StringResponse(dat);
					}
				});
			});
	}

}
