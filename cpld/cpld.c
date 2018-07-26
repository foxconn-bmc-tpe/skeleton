/*
Please get the JEDEC file format before you read the code
*/

#include <stdio.h>
#include <sys/ioctl.h>
#include <sys/types.h>
#include <fcntl.h>
#include <unistd.h>
#include <errno.h>
#include <stdlib.h>
#include <getopt.h>
#include <string.h>
#include <termios.h>

#include <sys/mman.h>
#include "lattice.h"
#include "ast-jtag.h"

/*************************************************************************************/
int lattice_get_id(unsigned int *id);
int lattice_get_id_pub(unsigned int *id);
/*************************************************************************************/
static void
usage(FILE *fp, int argc, char **argv)
{
	fprintf(fp,
		"Usage: %s [options]\n\n"
		"Options:\n"
		" -h | --help                   Print this message\n"
		" -i | --idle                   jtag go idle\n"
		" -e | --erase                  Erase cpld\n"
		" -p | --program                Program cpld and verify\n"
		" -v | --verify                 verifiy cpld image with file\n"
		" -r | --read                   Read cpld image to file\n"
		" -d | --debug                  debug mode\n"		
		" -f | --frequency                  frequency\n"		
		" -s | --software               sw mode\n"				
		"",
		argv[0]);
}

static const char short_options [] = "dshiep:v:r:f:";



static const struct option
long_options [] = {
        { "help",       	no_argument,            	NULL,   	'h' },
        { "idle",       	no_argument,            	NULL,   	'i' },
        { "erase",	no_argument,            	NULL,   	'e' },        
        { "program",	required_argument,      	NULL,   	'p' },
        { "verify",     	required_argument,      	NULL,   	'v' },
        { "read",       	required_argument,      	NULL,   	'r' },
        { "debug",      	no_argument,            	NULL,   	'd' },
        { "software",   no_argument,            	NULL,   	's' },        
	{ "fequency",	required_argument,		NULL,	'f' },
        { 0, 0, 0, 0 }
};

struct cpld_dev_info *cur_dev;
xfer_mode mode = HW_MODE;
int debug = 0;

/*********************************************************************************/
/*					LATTICE PROGRAMMING													*/
/*********************************************************************************/
/* JTAG_get_idcode(): returns the JTAG device's IDCODE
The first 32bits in receive buffer is IDCODE after you send IDCODE command to device
*/
int lattice_get_id(unsigned int *id)
{
	unsigned int tdo;
	//SIR	8	TDI  (16);
	tdo = ast_jtag_sir_xfer(0, LATTICE_INS_LENGTH, IDCODE);

	if(debug)
		printf("sir id,  tdo :%x \n",tdo);

	ast_jtag_tdo_xfer(0, 32, id);

//	printf("get id : %x \n", *id);
	return 0;
}

int lattice_get_id_pub(unsigned int *id)
{
	unsigned int tdo;
	//SIR	8	TDI  (16);
	tdo = ast_jtag_sir_xfer(0, LATTICE_INS_LENGTH, IDCODE_PUB);

	ast_jtag_tdo_xfer(0, 32, id);

//	printf("get id : %x \n", *id);
	return 0;
}

/*********************************************************************************/

#define ARRAY_SIZE(x) (sizeof(x) / sizeof((x)[0]))


/*************************************************************************************/
int main(int argc, char *argv[])
{
	int i;
	char option;
	char in_name[100]="", out_name[100]="";
	FILE *fp_in;
	int erase = 0, program = 0, verify = 0, gidle=0;
	unsigned int freq = 0;
	unsigned int jtag_freq = 0;

	unsigned int dev_id;

	while((option=getopt_long(argc, argv, short_options, long_options, NULL))!=(char)-1){
//		printf("option is c %c\n", option);
		switch(option){
			case 'h':
				usage(stdout, argc, argv);
				exit(EXIT_SUCCESS);
				break;
			case 'i':
				gidle = 1;
				break;				
			case 'e':
				erase = 1;
				break;
			case 'p':
				program = 1;
				strcpy(in_name, optarg);
				if(!strcmp(in_name, "")){
					printf("No input file name!\n");
					usage(stdout, argc, argv);
					exit(EXIT_FAILURE);
				}
				break;
			case 'v':
				verify = 1;
				strcpy(in_name, optarg);
				if(!strcmp(in_name, "")){
					printf("No input file name!\n");
					usage(stdout, argc, argv);
					exit(EXIT_FAILURE);
				}
				break;
			case 'r':
				//read = 1;
				strcpy(out_name, optarg);
				if(!strcmp(out_name, "")){
					printf("No out file name!\n");
					usage(stdout, argc, argv);
					exit(EXIT_FAILURE);
				}
				break;					
			case 'd':
				debug = 1;
//				printf("debug is %d\n",debug);
				break;
			case 'f':
				freq = atol(optarg);
				printf("frequency %d\n",freq);
				break;				
			case 's':
				mode = SW_MODE;
//				printf("sw_mode enable");
				break;					
			default:
				usage(stdout, argc, argv);
				exit(EXIT_FAILURE);
		}
	}

	
//	system("echo 104 > /sys/class/gpio/export");
//	system("echo out > /sys/class/gpio/gpio104/direction");
//	system("echo 0 > /sys/class/gpio/gpio104/value");
/////////////////////////////////////////////////////////////////////
	if(ast_jtag_open())
		exit(1);

	//show current ast jtag configuration 
	jtag_freq = ast_get_jtag_freq();
	
	if(jtag_freq == 0) {
		perror("Jtag freq error !! \n");
		exit(1);
	}

	if(freq) {
		ast_set_jtag_freq(freq);
		printf("Mode : %s , JTAG Set Freq %d", mode? "SW":"HW", freq);
	} else {
		printf("Mode : %s , JTAG Freq %d", mode? "SW":"HW", jtag_freq);
	}

	if(debug) printf(", debug mode \n");
	else printf("\n");
	
	ast_jtag_run_test_idle( 1, 0, 0);

#if 1
#if 0
	lattice_get_id(&dev_id);
#else
	lattice_get_id_pub(&dev_id);
#endif
#endif
//	dev_id = 0x012B5043;

	for(i=0; i< ARRAY_SIZE(lattice_device_list); i++) {
		if(dev_id == lattice_device_list[i].dev_id)
			break;
	}
	
	if(i == ARRAY_SIZE(lattice_device_list)) {
		printf("AST LATTICE Device - UnKnow : %x \n",dev_id);
		cur_dev = NULL;
		return -1;
	} else {
		cur_dev = &lattice_device_list[i];
		printf("AST LATTICE Device : %s \n",cur_dev->name);
	}		
	
	if((program) || (verify)) {
		fp_in = fopen(in_name, "rb");
		if(!fp_in) {
			fprintf(stderr, "Cannot open '%s': %d, %s\n", in_name, errno, strerror(errno));
			goto out;
		}
	}

	if(debug) printf("function dispatch gidle %d, erase %d, program %d, verify %d\n", gidle, erase, program, verify);

	if(erase) {
		printf("Starting to Erase Device . . . ");
		cur_dev->cpld_erase();
	} else if (gidle) {
		printf("Run reset idle \n");
		ast_jtag_run_test_idle( 1, 0, 0);
	} else if (program) {
		printf("Program : JEDEC file %s\n", in_name);
		cur_dev->cpld_program(fp_in);
	} else if (verify) {
		printf("Verify : JEDEC file %s\n", in_name);
		cur_dev->cpld_verify(fp_in);
	} else {
		usage(stdout, argc, argv);
	}

out:
	if((program) || (verify))
		fclose(fp_in);	
	
	ast_jtag_close();

    return 0;
}
