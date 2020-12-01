# File System
### Designed and implemented an emulated disk<br/>
 - Byte array D[64][512] to represent the emulated disk
 - Disk access functions read_block() and write_block()
  
### Designed and implemented a File System
 - Data structures I[512], O[512], M[512], OFT[4]
 - Functions: create(), destroy(), open(), close(), read(), write(), seek(), directory()
 - Auxiliary functions: init(), read_memory(), write_memory()
 
### Designed and implemented a Shell to process command line inputs
 - cr name
    - create a new file with the name
 - de name
    - destroy the named file name
 - op name
    - open the named file name for reading and writing
 - l index
    - close the specified file index
 - rd index mem count
    - copy count bytes from open file index (starting from current position) to memory M (starting at location M[mem])
 - wr index mem count
    - copy count bytes from memory M (starting at location M[mem]) to open file index (starting from current position) 
 - sk index pos
    - seek: set the current position of the specified file index to pos
 - dr
    - directory: list the names and lengths of all files
 - in 
    - initialize the system to the original starting configuration
 - rm mem count
    - copy count bytes from memory M staring with position mem to output device (terminal or file)
 - wm mem str
    - copy string str into memory M starting with position mem from input device (terminal or file)
