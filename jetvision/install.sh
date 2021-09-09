build_gst_python()
{
	# Builds and installs gst-python (python bindings for gstreamer)
	sudo apt-get install python3-dev python-gi-dev libgstreamer1.0-dev -y;
	export GST_LIBS="-lgstreamer-1.0 -lgobject-2.0 -lglib-2.0";
	export GST_CFLAGS="-pthread -I/usr/include/gstreamer-1.0 -I/usr/include/glib-2.0 -I/usr/lib/x86_64-linux-gnu/glib-2.0/include";
	git clone https://github.com/GStreamer/gst-python.git /tmp/gst-python;
	cd /tmp/gst-python;
	git checkout 1a8f48a;
	./autogen.sh PYTHON=python3;
	./configure PYTHON=python3;
	make -j$(nproc);
	sudo make install; # TODO: is sudo necessary?
}

build_ds_bindings()
{
    sudo apt install cuda-nvrtc-10-2 -y;
    cd /opt/nvidia/deepstream/deepstream/lib;
    sudo python3 setup.py install;
}

download_models()
{
    MODEL_DIR=$HOME/.jetvision-files/models;
	mkdir -p $MODEL_DIR/peoplenet;
    wget --content-disposition https://api.ngc.nvidia.com/v2/models/nvidia/tlt_peoplenet/versions/pruned_v2.0/zip -O /tmp/tlt_peoplenet_pruned_v2.0.zip -o /dev/null;
    unzip /tmp/tlt_peoplenet_pruned_v2.0.zip -d $MODEL_DIR/peoplenet/tlt_peoplenet_pruned_v2.0
}

echo "Installing..."

# Build and install python bindings
build_gst_python
# Install ds bindings for python
build_ds_bindings
# Downloads pretrained models from tlt
download_models


