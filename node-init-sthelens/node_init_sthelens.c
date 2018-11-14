#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <string.h>
#include <sys/types.h>
#include <dirent.h>
#include "i2c-dev.h"

#define MAX_I2C_DEV_LEN 32
#define PMBUS_SLAVE_ADDR 0x58
#define PHYSICAL_I2C 8
#define PMBUS_NUMBER 6

void pmbus_scan()
{

    char buff_path[256] = "";
    int i;
    int file, file1;
    char filename[MAX_I2C_DEV_LEN] = {0};
    int bus;
    int rc = 0;
    int res;
    sleep(40);
    while(1) {
        for(i=0;i<PMBUS_NUMBER;i++) {
            /* Init pmbus node */
            bus = PHYSICAL_I2C + i;
			printf ("[DEBUGMSG] bus : %d\n", bus);
            sprintf(filename,"/dev/i2c-%d",bus);
            file = open(filename,O_RDWR);
            rc = ioctl(file, I2C_SLAVE, PMBUS_SLAVE_ADDR);
			printf ("[DEBUGMSG] rc : %d\n", rc);
            if (rc == 0) {
                res = i2c_smbus_read_byte(file);
				printf ("[DEBUGMSG] res : %d\n", res);
                if (res >= 0) {
                    sprintf(buff_path, "echo pmbus 0x58 > /sys/bus/i2c/devices/i2c-%d/new_device", bus);
					printf ("[DEBUGMSG] buff_path : %s\n", buff_path);
                    system(buff_path);
					sprintf(filename,"/sys/bus/i2c/drivers/pmbus/%d-0058",bus);
					file1 = open(filename,O_RDWR);
					if (file1 != 0) {
						sprintf(buff_path, "echo %d-0058 > /sys/bus/i2c/drivers/pmbus/bind", bus);
						printf ("[DEBUGMSG] buff_path : %s\n", buff_path);
						system(buff_path);
					}
					close(file1);
                }
            }
            close(file);
        }
        sleep(10);								// delay 10ms
    }
	printf ("[DEBUGMSG] leave while loop");
	/* fix-mac & fix-guid */
    printf("fix-mac & fix-guid start");
    system("/usr/sbin/mac_guid.py --fix-mac");
    system("/usr/sbin/mac_guid.py --fix-guid");
}

int main(void)
{
    pmbus_scan();
    return 0;
}

