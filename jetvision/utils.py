import glob


def find_dev_by_name(query: str):
    v4l_name_files = glob.glob("/sys/class/video4linux/video*/name")
    v4l_name_files = sorted(v4l_name_files)

    dev2name = {}
    for nf in v4l_name_files:
        with open(nf) as f:
            dev = nf.split("/")[-2]
            name = f.read()
            name = name.strip("\n")  # remove newline from the end of device name
            dev2name["/dev/" + dev] = name

    name2dev = {v: k for k, v in dev2name.items()}

    matching = []
    for (d, n) in dev2name.items():
        if query in n:
            matching.append(d)

    return matching


print(find_dev_by_name("imx185"))
print(find_dev_by_name("ar0234"))
