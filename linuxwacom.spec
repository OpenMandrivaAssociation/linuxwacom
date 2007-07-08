%define version  0.7.8
%define fversion 0.7.8
%define fname    %{name}-%{fversion}
%define raw_libname wacom
%define libname  %mklibname %raw_libname 0

%define build_dkms 0
%{?_with_dkms: %global build_dkms 1}

%if %mdkversion < 200800
%define build_dkms 1
%endif


Name:    linuxwacom
Version: %version
Release: %mkrel 2
Summary: Tools to manage Wacom tablets
License: LGPL
Group:   System/X11
URL:     http://linuxwacom.sourceforge.net
Source0: http://prdownloads.sourceforge.net/linuxwacom/%{fname}.tar.bz2
BuildRoot:     %{_tmppath}/%{name}-%{version}-root
BuildRequires: X11-devel, libxi-devel, x11-server-devel, ncurses-devel
BuildRequires: tcl-devel tk-devel
# RH patches:
#Patch2:  linuxwacom-fsp.patch
#Patch4:  linuxwacom-0.7.2-delibcwrap.patch

%description 
X.org XInput drivers, diagnostic tools and documentation for configuring
and running Wacom tablets.

%package -n %libname
Summary: Wacom Drivers
Group:   System/X11
Requires: %{name} = %{version}

%description -n %libname
Libraries for managing the Wacom tablets.

%package -n %libname-devel
Summary: Development libraries and header files for linuxwacom 
Group: Development/C
Requires: %{libname} = %{version}
#Requires: lib%{raw_libname} = %{version}
Provides: lib%{raw_libname}-devel = %{version}

%description -n %libname-devel
Development libraries and header files required for developing applications
that manipulate Wacom tablets settings.

%if %{build_dkms}
%package -n dkms-wacom
Summary:        Wacom kernel module
Group:          System/Kernel and hardware
Requires(post):  dkms
Requires(preun): dkms

%description -n dkms-wacom
Latest version of wacom kernel module as well as hid-core, for support
for latest Wacom tablets.
%endif

%prep
%setup -q -n %{fname}

#%patch2 -p1 -b .fsp
#%patch4 -p0 -b .delibcwrap

%build
# determine whether we are on 64-bit platforms
# XXX their test is not fully correct because it assumes 64-bit
# platforms are lib64 (which is also a required check)
echo "int main(void) { return ! (sizeof(void *) == 8); }" | %__cc -xc -o test64 -
./test64 && XServer64="--enable-xserver64"
rm -f test64

%configure2_5x --with-xorg-sdk=/usr --with-xlib=%{_libdir} --enable-dlloader $XServer64

export CFLAGS="$RPM_OPT_FLAGS"
%make

%install
rm -rf $RPM_BUILD_ROOT

%makeinstall_std x86moduledir=%{_libdir}/xorg/modules/input
rm -f  $RPM_BUILD_ROOT%{_libdir}/*.la
rm -rf $RPM_BUILD_ROOT%{_prefix}/lib/TkXInput/%{*.a,la}

%if %{build_dkms}
# install wacom kernel module sources
mkdir -p $RPM_BUILD_ROOT%{_usr}/src/wacom-%{version}
cp src/2.6.16/* $RPM_BUILD_ROOT%{_usr}/src/wacom-%{version}/
cat > $RPM_BUILD_ROOT%{_usr}/src/wacom-%{version}/dkms.conf << EOF
PACKAGE_NAME=wacom
PACKAGE_VERSION=%{version}
MAKE="make WCM_OPTION_WACOM=yes -C \$kernel_source_dir M=\$dkms_tree/\$PACKAGE_NAME/\$PACKAGE_VERSION/build"
DEST_MODULE_LOCATION[0]=/kernel/drivers/usb/input/
BUILT_MODULE_NAME[0]=wacom
AUTOINSTALL=yes
EOF
%endif

%clean
rm -rf $RPM_BUILD_ROOT

%post   -n %libname -p /sbin/ldconfig

%postun -n %libname -p /sbin/ldconfig

%if %{build_dkms}
%post -n dkms-wacom
set -x
/usr/sbin/dkms --rpm_safe_upgrade add -m wacom -v %{version}
/usr/sbin/dkms --rpm_safe_upgrade build -m wacom -v %{version}
/usr/sbin/dkms --rpm_safe_upgrade install -m wacom -v %{version}

%preun -n dkms-wacom
# rmmod can fail
/sbin/rmmod %{wacom} hidcore >/dev/null 2>&1
set -x
/usr/sbin/dkms --rpm_safe_upgrade remove -m wacom -v %{version} --all || :
%endif

%files 
%defattr(-,root,root,-)
%doc AUTHORS ChangeLog NEWS
%{_libdir}/xorg/modules/input/wacom_drv.*o
%{_libdir}/TkXInput
%{_bindir}/*
%{_mandir}/man4/*.bz2

%files -n %libname
%defattr(-,root,root,-)
%doc LGPL
%{_libdir}/lib*so.*

%files -n %libname-devel
%defattr(-,root,root,-)
%{_includedir}/*
%{_libdir}/lib*.a
%{_libdir}/lib*.so

%if %{build_dkms}
%files -n dkms-wacom
%defattr(-,root,root)
%{_usr}/src/wacom-%{version}
%endif
