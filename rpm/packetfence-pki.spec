%global __os_install_post %(echo '%{__os_install_post}' | sed -e 's!/usr/lib[^[:space:]]*/brp-python-bytecompile[[:space:]].*$!!g')
%define serverroot /usr/local/packetfence-pki
Name: packetfence-pki
Version: %{ver}
Release: 1%{?dist}
Summary: packetfence-pki

Group:	System/Servers
License: GPL
Buildarch: noarch
URL: https://github.com/inverse-inc/packetfence-pki
Source0: packetfence-pki-%{version}.tar.bz2
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root

BuildRequires:	python
Requires: httpd, mod_wsgi, mod_ssl, python, python-django-bootstrap3, django-countries, python-django-rest-framework, python-django, pyOpenSSL >= 0.14, python-ldap, python-pyasn1 >= 0.1.7 , python-pyasn1-modules >= 0.1.7, python-six

%description
Small PKI to integrate with PacketFence for certificates generation when using EAP-TLS

%prep
%setup -q

%build
rm -rf $RPM_BUILD_ROOT


%install
make PREFIX=$RPM_BUILD_ROOT%{serverroot} PREFIXLIB=$RPM_BUILD_ROOT%{serverroot} UID='-o nobody' GID='-g nobody' install
install -d -m0700 $RPM_BUILD_ROOT/etc/init.d
install -m0755 rpm/%{name} $RPM_BUILD_ROOT/etc/init.d/%{name}

%clean
rm -rf %{buildroot}

%pre

if ! /usr/bin/id pf &>/dev/null; then
        /usr/sbin/useradd -r -d "/usr/local/packetfence-pki" -s /bin/sh -c "PacketFence" -M pf || \
                echo Unexpected error adding user "pf" && exit
fi

%post
if [ -f %{serverroot}/conf/server.crt ] ; then
        echo "certificate exist do nothing"
else
        openssl req -x509 -new -nodes -days 365 -batch\
        -out %{serverroot}/conf/server.crt\
        -keyout %{serverroot}/conf/server.key\
        -nodes -config %{serverroot}/conf/openssl.cnf
fi
if [ -f %{serverroot}/db.sqlite3 ] ; then
        echo "Database is there do nothing"
else
cd %{serverroot} && python manage.py syncdb --noinput
fi
chown -R pf.pf %{serverroot}
chown pf.pf %{serverroot}/conf/httpd.conf
chmod 600 %{serverroot}/conf/httpd.conf

%preun
if [ $1 -eq 0 ] ; then
        /sbin/service packetfence-pki stop &>/dev/null || :
        /sbin/chkconfig --del packetfence-pki
fi

%postun
if [ $1 -eq 0 ]; then
        if /usr/bin/id pf &>/dev/null; then
               /usr/sbin/userdel pf || %logmsg "User \"pf\" could not be deleted."
        fi
fi

%files
%defattr(-,apache,apache,-)
%config(noreplace) %{serverroot}/conf/*
%{serverroot}/inverse/*
%{serverroot}/pki/*
%{serverroot}/manage.py
%{serverroot}/initial_data.json
%dir %{serverroot}/logs
%dir %{serverroot}/ca
%defattr(-,root,root)
/etc/init.d/%{name}

%changelog
