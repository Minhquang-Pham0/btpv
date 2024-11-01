Name:           password-vault
Version:        0.1.0
Release:        1%{?dist}
Summary:        Secure Password Management System

License:        Proprietary
URL:            http://saoc.snc/password-vault
Source0:        %{name}-%{version}.tar.gz

BuildRequires:  python39-devel
BuildRequires:  postgresql-devel
BuildRequires:  gcc
Requires:       python39
Requires:       postgresql-server
Requires:       postgresql-contrib

%description
A secure password management system with group sharing capabilities.

%prep
%setup -q

%install
rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT/opt/%{name}
mkdir -p $RPM_BUILD_ROOT/etc/%{name}
mkdir -p $RPM_BUILD_ROOT/var/log/%{name}
mkdir -p $RPM_BUILD_ROOT/var/lib/%{name}
mkdir -p $RPM_BUILD_ROOT/etc/systemd/system

# Copy application files
cp -r backend/* $RPM_BUILD_ROOT/opt/%{name}/
cp backend/.env.template $RPM_BUILD_ROOT/etc/%{name}/config.env
cp backend/scripts/install.sh $RPM_BUILD_ROOT/opt/%{name}/install.sh

%files
%defattr(-,root,root,-)
/opt/%{name}
%config(noreplace) /etc/%{name}
%dir /var/log/%{name}
%dir /var/lib/%{name}

%pre
# Create user and group if they don't exist
getent group password-vault >/dev/null || groupadd -r password-vault
getent passwd password-vault >/dev/null || \
    useradd -r -g password-vault -d /opt/password-vault -s /sbin/nologin \
    -c "Password Vault Service Account" password-vault

%post
# Run installation script
/opt/%{name}/install.sh

%preun
if [ $1 -eq 0 ] ; then
    systemctl stop password-vault >/dev/null 2>&1 || :
    systemctl disable password-vault >/dev/null 2>&1 || :
fi

%postun
if [ $1 -eq 0 ] ; then
    userdel password-vault >/dev/null 2>&1 || :
    groupdel password-vault >/dev/null 2>&1 || :
fi

%changelog
* Fri Nov 1 2024 Your Name <your.email@domain.com> - 0.1.0-1
- Initial package release