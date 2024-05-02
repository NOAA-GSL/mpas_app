help([[
This module loads the python environment for running the MPAS App on 
the NOAA RDHPC machine Hera
]]) 
 
whatis([===[Loads libraries needed for running the MPAS App on Hera ]===]) 

load("rocoto")
load("conda")

if mode() == "load" then
    LmodMsgRaw([===[Please do the following to activate conda:
	>conda activate mpas_app
]===])
end

