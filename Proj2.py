import sys, os

D = []
OFT = []
M = []
I = []
O = []
fdCount = 0;

def init():
    global fdCount
    D.clear()
    OFT.clear()
    M.clear()
    I.clear()
    O.clear()
    fdCount = 0;

    for i in range(64): # D[64][512]
        D.append([''] * 512)

    for i in range(1,7): # D[1] to D[6] are fd blocks
        for j in range(0,509,4):
            D[i][j] = -1

    D[1][0] = 0 # fd 0 is initially length 0
    D[1][1] = 7 # fd 0 initally has block 7 allocated

    for i in range(len(D[0])): # D[0] to D[7] allocated, D[8] to D[63] are free
        if i >= 0 and i <= 7:
            D[0][i] = 1
        else:
            D[0][i] = 0

    for i in range(len(D[7])):
        D[7][i] = '0' # CHANGED HERE from '0'

    for i in range(0,4):
        if i == 0:
            OFT.append({
                "RW": [],
                "POSITION": 0,
                "FSIZE": 0,
                "FDINDEX": 0
            })
        else:
            OFT.append({
                "RW": [],
                "POSITION": -1,
                "FSIZE": -1,
                "FDINDEX": -1
            })

    OFT[0]["RW"] = D[7]

    for i in range(0,512):
        M.append('')

    print("system initialized")

def create(name):
    global fdCount

    if len(name) > 3:
        print("error")
        return

    # See if file already exists
    if fileExists(name):
        print("error")
        return

    if fdCount > 192:
        print("error")
        return

    # Search for free file descriptor
    fdBlock, fdIndex = findFreeFD()
    if fdBlock == -1 and fdIndex == -1:
        print("error")
        return

    # If size of file is 512 or 1024, need to create a new block
    if D[1][0] == 512 or D[1][0] == 1024:
        newBIndex = getNewBlock()
        if newBIndex != -1:
            if assignNewBlock(1,0,newBIndex) == False:
                print("error")
                return
            for i in range(len(D[newBIndex])):
                D[newBIndex][i] = '0'
            #Need to add to OFT HERE

    # Search for free entry in directory
    # Seek D[7] to 0
    dirList = list((x for x in D[1][1:4] if type(x) == int))
    for dir in dirList: # Get list of blocks directory has
        for i in range(0,505,8): # Need to change this later to start on the position in OFT
            if D[dir][i] != '0' and i == 504 and len(dirList) == 3 and dir == dirList[-1]: #If last 8 bytes of 3rd block
                print("error")
                return

            if D[dir][i] == '0': # Space in directory
                # Assigning descriptor to file
                D[fdBlock][fdIndex] = 0  # -1 to 0 to indicate new file is empty

                nameList = list(name)
                for j in range(0, 4 - len(nameList)): # Append end of string char if name is < 4 chars
                    nameList.append('/')
                nameList.append(fdIndex + ((fdBlock-1)*512))
                for j in range(0,3):
                    nameList.append('')

                for k,letter in enumerate(nameList,i): # Overwriting
                    D[dir][k] = letter
                break

    D[1][0] += 8 # fd[0] (directory file) size is now 8 more bytes
    fdCount += 1
    print(name, "created")

def delete(name):
    global fdCount

    fdBlock, fdIndex,dir, i = findName(name)
    if fdBlock == -1 and fdIndex == -1:
        print("error")
        return
    fdIndex = fdIndex%512

    D[fdBlock][fdIndex] = -1 # Mark descriptor i as free by setting the size field to −1

    blockList = getBlocks(fdBlock,fdIndex)
    if blockList: # If there are blocks allocated
        for block in blockList: # For each nonzero block number in the descriptor, update bitmap to reflect the freed block
            D[0][block] = 0
        for block in range(fdIndex+1,fdIndex+4): # Set all nonzero block numbers to 0
            D[fdBlock][block] = ''

    for space in range(i,i+8): # Mark the directory entry as free by setting the name field to '0'
        D[dir][space] = '0'

    fdCount -= 1
    print(name,"destroyed")

def myOpen(name):

    fdBlock, fdIndex,dir,i = findName(name)
    if fdBlock == -1 and fdIndex == -1:
        print("error")
        return

    for OFTIndex in range(0,4):
        if OFT[OFTIndex]["FDINDEX"] == -1:
            OFT[OFTIndex]["RW"] = []
            OFT[OFTIndex]["POSITION"] = 0
            OFT[OFTIndex]["FSIZE"] = D[fdBlock][fdIndex%512]
            OFT[OFTIndex]["FDINDEX"] = fdIndex # Setting true fdIndex (Can be > 508)

            if OFT[OFTIndex]["FSIZE"] == 0:
                block = getNewBlock()
                if block != -1:
                    D[fdBlock][fdIndex%512+1] = block
                    D[0][block] = 1
                    OFT[OFTIndex]["RW"] = D[D[fdBlock][fdIndex%512 + 1]]
            else:
                OFT[OFTIndex]["RW"] = D[D[fdBlock][fdIndex%512+1]]

            print(name,"opened",OFTIndex)
            return

    print("error")

def myClose(i):
    i *= 4

    for OFTIndex in range(0,4):
        if OFT[OFTIndex]["FDINDEX"] == i:

            fdBlock = (i//512)+1

            # Determine which block is currently held in the r/w buffer and copy the current buffer contents to the block
            #Block is known based on position, position%512
            D[D[fdBlock][(i%512)+(OFT[OFTIndex]["POSITION"]//512)+1]] = OFT[OFTIndex]["RW"] #Not really needed

            D[fdBlock][i%512] = OFT[OFTIndex]["FSIZE"] # Copy the file size from the OFT to the descriptor

            OFT[OFTIndex]["RW"] = [] #2 lines above is needed if this is here
            OFT[OFTIndex]["FDINDEX"] = -1 #Mark the OFT entry as free
            OFT[OFTIndex]["POSITION"] = -1
            OFT[OFTIndex]["FSIZE"] = -1

            print(i//4 ,"closed")
            return
    print("error")

def read(i,m,n):

    if OFT[i]["FDINDEX"] == -1:
        print("error")
        return

    RWPosition = OFT[i]["POSITION"]%512
    pos = RWPosition

    emptyCt = 0;
    for c in range(0,n): # Until is reached
        if pos == 512 or pos == 1024:
            fdBlock = (OFT[i]["FINDEX"] // 512) + 1
            OFT[i]["RW"] = D[D[fdBlock][(OFT[i]["FINDEX"] % 512) + (OFT[i]["POSITION"] // 512) + 2]]
            pos = 0
        if(OFT[i]["RW"][pos] == ''):
            emptyCt += 1
        else:
            M[m] = OFT[i]["RW"][pos]
        # M[m] = OFT[i]["RW"][pos]
        m += 1
        pos += 1
    OFT[i]["POSITION"] += n
    print(n-emptyCt,"bytes read from",i)

def write(i,m,n):

    if OFT[i]["FDINDEX"] == -1:
        print("error")
        return

    #The function write(i, m, n) copies n bytes from memory M starting at location m to the open file i, starting at the current position.
    RWPosition = OFT[i]["POSITION"]%512
    pos = RWPosition
    blocketh = RWPosition//512

    for c in range(0,n):
        if pos == 512 or pos == 1024: # End of buffer
            blockList = getBlocks((OFT[i]["FDINDEX"]//508)+1,OFT[i]["FDINDEX"]%512)
            if len(blockList) > blocketh+1: # A sequential block exists
                # Write OFT[i]["RW"] to blocketh and get blocketh+1
                D[blockList[blocketh]] = OFT[i]["RW"]
                OFT[i]["RW"] = D[blockList[blocketh+1]]
                pos = 0
                blocketh += 1
            elif len(blockList) < 3 and blocketh+1 == len(blockList): # allocate another free block
                block = getNewBlock()
                if block != -1:
                    D[0][block] = 1
                    D[(OFT[i]["FDINDEX"]//508)+1][OFT[i]["FDINDEX"]%512 + 1 + blocketh + 1] = block
                    OFT[i]["RW"] = D[block]
                    pos = 0
                    blocketh += 1
                # Else break
            #Else break

        OFT[i]["RW"][pos] = M[m]
        m += 1
        pos += 1

    OFT[i]["POSITION"] += n
    if(OFT[i]["POSITION"] > OFT[i]["FSIZE"]):
        OFT[i]["FSIZE"] = OFT[i]["POSITION"]
        D[(OFT[i]["FDINDEX"]//508)+1][OFT[i]["FDINDEX"]%512] = OFT[i]["FSIZE"]

    # If c == n print n, else print n - c
    print(n,"bytes written to",i)

def seek(i,p):

    if OFT[i]["FDINDEX"] == -1:
        print("error")
        return

    if p > OFT[i]["FSIZE"]:
        print("error")
        return

    blocketh = p//512
    if blocketh != OFT[i]["POSITION"]//512:
        fdBlock = (OFT[i]["FDINDEX"]//508) + 1
        fdIndex = OFT[i]["FDINDEX"] % 512
        D[D[fdBlock][fdIndex + 1 + OFT[i]["POSITION"]//512]] = OFT[i]["RW"]
        OFT[i]["RW"] = D[D[fdBlock][fdIndex + 1 + blocketh]]

    OFT[i]["POSITION"] = p
    print("position is",p)

def directory():
    dirList = list((x for x in D[1][1:4] if type(x) == int))
    for dir in dirList:  # Get list of blocks directory has
        for i in range(0, 505, 8):
            if D[dir][i] != '0':
                strList = D[dir][i:i+4]
                name = "";
                for ch in strList:
                    if ch != '/':
                        name += ch

                #Getting file size
                fdIndex = D[dir][i+4]
                fdBlock = fdIndex // 508 + 1
                fsize = D[fdBlock][fdIndex%512]

                print(name,fsize,end=' ')

def read_memory(m,n):
    mList = M[m:m+n]
    sent = ""
    for ch in mList:
        if ch == '':
            sent += ' '
        else:
            sent += ch
    print(sent)

def write_memory(m,s):
    i = 0
    for ch in list(s):
        M[m+i] = ch
        i+=1
    print(i,"bytes written to M")

# HELPER FUNCTIONS
def findFreeFD():
    for i in range(1,7):
        for j in range(0,509,4):
            if D[i][j] == -1:
                return i,j
    return -1,-1

def fileExists(name):
    # Seek D[7] to 0
    fName = ""
    for i in range(0,505, 8):
        temp = ""
        temp = temp.join(D[7][i:i+4])
        for e in temp:
            if e != '0' and e != '/':
                fName += e
        if fName == name:
            return True
    return False

def getNewBlock():
    for i in range(len(D[0])):
        if D[0][i] == 0:
            return i
    return -1

def assignNewBlock(fdBlock,fdIndex,newBIndex):
    for i in range(fdIndex+1,fdIndex+4):
        if D[fdBlock][i] == '':
            D[fdBlock][i] = newBIndex
            return True;
    return False;

def getBlocks(fdBlock,fdIndex):
    blockList = list((x for x in D[fdBlock][fdIndex+1:fdIndex+4] if type(x) == int))
    return blockList

def printD():
    for i,row in enumerate(D,0):
        print("D[" + str(i) + "]:",row)

def printOFT():
    for i in OFT:
        print(i)

def findName(name):
    nameList = list(name)
    for j in range(0, 4 - len(nameList)):  # Append end of string char if name is < 4 chars
        nameList.append('/')

    dirList = getBlocks(1, 0)
    for dir in dirList:
        for i in range(0, 505, 8):
            nameField = D[dir][i:i + 4]
            if nameList == nameField:
                fdIndex = D[dir][i + 4]
                fdBlock = (fdIndex // 512) + 1
                return fdBlock,fdIndex,dir,i # Returns true fdIndex (Can be > than 508)
    return -1, -1, -1, -1


if __name__ == "__main__":

    with open('/Users/JustinFu/Documents/CompSci 143B/Proj2/input.txt') as fp:
        line = fp.readline()
        while(line):
            cmd = list(line.split())
            line = fp.readline()

            if cmd:
                if cmd[0] == "in":
                    init()
                elif cmd[0] == "cr":
                    create(cmd[1])
                elif cmd[0] == "de":
                    delete(cmd[1])
                elif cmd[0] == "op":
                    myOpen(cmd[1])
                elif cmd[0] == "cl":
                    if cmd[1].isdigit() == False:
                        print("error")
                        continue
                    myClose(int(cmd[1]))
                elif cmd[0] == "rd":
                    read(int(cmd[1]),int(cmd[2]),int(cmd[3]))
                elif cmd[0] == "wr":
                    write(int(cmd[1]),int(cmd[2]),int(cmd[3]))
                elif cmd[0] == "sk":
                    seek(int(cmd[1]),int(cmd[2]))
                elif cmd[0] == "dr":
                    directory()
                    print()
                elif cmd[0] == "rm":
                    read_memory(int(cmd[1]),int(cmd[2]))
                elif cmd[0] == "wm":
                    inp = ""
                    for i in range(2,len(cmd)):
                        inp += cmd[i]
                        if i != len(cmd)-1:
                            inp += " "
                    write_memory(int(cmd[1]),inp)
            else:
                print()