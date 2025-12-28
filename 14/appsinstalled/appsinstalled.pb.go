// Code generated manually for homework usage. DO NOT EDIT.

package appsinstalled

import proto "github.com/golang/protobuf/proto"

// UserApps mirrors appsinstalled.proto.
type UserApps struct {
	Apps []uint32 `protobuf:"varint,1,rep,name=apps" json:"apps,omitempty"`
	Lat  *float64 `protobuf:"fixed64,2,opt,name=lat" json:"lat,omitempty"`
	Lon  *float64 `protobuf:"fixed64,3,opt,name=lon" json:"lon,omitempty"`
}

func (m *UserApps) Reset() { *m = UserApps{} }

func (m *UserApps) String() string { return proto.CompactTextString(m) }

func (*UserApps) ProtoMessage() {}
