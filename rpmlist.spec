%define		rpmlist_rev 1.5
Summary:	RPM browser
Summary(pl.UTF-8):Przeglądarka RPM-ów
Name:		rpmlist
Version:	%{rpmlist_rev}
Release:	1
License:	GPL
Group:		Applications/System
Source0:	%{name}.py
Requires:	python-poldek
Requires:	python-rpm
BuildArch:	noarch
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%description
This package contains a HTTP server which provides information about
installed RPMs and those from poldek's databases. By default program
listens on port 9999, but you could change this.
For example: rpmlist 7777.

%description -l pl.UTF-8
Ten pakiet zawiera serwer www dostarczający informacji o
zainstalowanych pakietach RPM oraz o RPM-ach z baz poldka. Domyślnie
serwer nasłuchuje na porcie 9999. Jeśli chcesz możesz to zmienić
uruchamiając rpmlist np. tak: rpmlist 7777


%prep
rev=$(awk '/^#.*Revision:.*Date/{print $3}' %{SOURCE0})
if [ "$rev" != "%rpmlist_rev" ]; then
	: Update rpmlist_rev define to $rev, and retry
	exit 1
fi

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT%{_bindir}
install %{SOURCE0} $RPM_BUILD_ROOT%{_bindir}/rpmlist

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(644,root,root,755)
%attr(755,root,root) %{_bindir}/*
