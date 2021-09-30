export LD_PRELOAD=/usr/lib/aarch64-linux-gnu/libgomp.so.1;
export OPENBLAS_CORETYPE=ARMV8; # Workaround of numpy/OpenBLAS bug on aarch64 https://github.com/numpy/numpy/issues/18131
export DISPLAY=:0; # To display over SSH
