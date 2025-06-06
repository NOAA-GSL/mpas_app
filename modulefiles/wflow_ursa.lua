help([[
This module loads the python environment for running the MPAS App on 
the NOAA RDHPC machine Ursa
]]) 
 
whatis([===[Loads libraries needed for running the MPAS App on Ursa ]===]) 

load("rocoto")
load("conda")

if mode() == "load" then
    LmodMsgRaw([===[Please do the following to activate conda:
	>conda activate mpas_app
]===])
end

